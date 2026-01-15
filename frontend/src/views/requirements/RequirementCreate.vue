<template>
  <div class="requirement-create">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        创建能力需求
      </template>
    </el-page-header>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>
            <el-icon><Document /></el-icon>
            需求录入
          </span>
          <el-tag type="info">文本输入或文件上传任选其一</el-tag>
        </div>
      </template>

      <el-form label-width="100px" @submit.prevent="handleSubmit">
        <el-form-item label="需求名称" required>
          <el-input
            v-model="title"
            placeholder="请输入需求名称"
            clearable
            @input="handleTitleInput"
          />
        </el-form-item>

        <!-- Tabs for Input Method -->
        <el-tabs v-model="activeTab" class="mb-20">
          <el-tab-pane label="文本输入" name="text">
            <el-form-item label="需求文本">
              <el-input
                v-model="textContent"
                type="textarea"
                :rows="10"
                placeholder="每行一个需求，例如：&#10;用户登录&#10;权限管理&#10;数据导出"
                @input="handleTextChange"
              />
            </el-form-item>
          </el-tab-pane>

          <el-tab-pane label="文件上传" name="file">
            <el-form-item>
              <el-upload
                ref="uploadRef"
                class="upload-demo"
                drag
                action="#"
                :auto-upload="false"
                :on-change="handleFileChange"
                :limit="1"
                :on-exceed="handleExceed"
                :on-remove="handleFileRemove"
                accept=".xlsx,.xls,.csv,.docx"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .xlsx, .xls, .csv, .docx 格式，文件大小不超过 10MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>

            <!-- File Info -->
            <div v-if="selectedFile" class="file-info">
              <el-descriptions :column="3" border size="small">
                <el-descriptions-item label="文件名">
                  {{ selectedFile.name }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(selectedFile.size) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件类型">
                  {{ getFileType(selectedFile.name) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-tab-pane>
        </el-tabs>

        <!-- Submit Buttons -->
        <el-form-item>
          <div class="button-group">
            <el-button
              type="primary"
              size="large"
              @click="handleSubmit"
              :loading="submitting"
              :disabled="!canSubmit"
            >
              <el-icon><Check /></el-icon>
              {{ submitButtonText }}
            </el-button>
            <el-button size="large" @click="handleClear">
              <el-icon><Delete /></el-icon>
              清空重置
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Parsing Error Alert -->
    <el-alert
      v-if="parsingError"
      type="error"
      title="文件解析错误"
      :description="parsingError"
      show-icon
      closable
      @close="parsingError = null"
      class="mt-20"
    />

    <!-- Preview -->
    <el-card v-if="textContent && activeTab === 'text'" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>需求预览</span>
          <el-tag>共 {{ previewLines }} 条</el-tag>
        </div>
      </template>
      <div class="preview-content">
        <div v-for="(line, index) in previewText" :key="index" class="preview-line">
          <el-tag size="small" class="mr-10">{{ index + 1 }}</el-tag>
          <span>{{ line }}</span>
        </div>
      </div>
    </el-card>

    <!-- Created Requirements -->
    <el-card v-if="createdRequirements.length > 0" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>已创建的需求</span>
          <el-tag type="success">共 {{ createdRequirements.length }} 条</el-tag>
        </div>
      </template>

      <el-table :data="createdRequirements" border max-height="400">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="item_text" label="需求内容" show-overflow-tooltip />
        <el-table-column prop="item_order" label="序号" width="80" />
      </el-table>

      <div class="mt-20 text-center">
        <el-button type="success" @click="handleGoToMatching">
          <el-icon><Connection /></el-icon>
          前往匹配分析
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Plus /></el-icon>
          创建更多需求
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMatchingStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import {
  Document,
  Check,
  Delete,
  UploadFilled,
  Connection,
  Plus
} from '@element-plus/icons-vue'
import type { RequirementItem } from '@/types'

const router = useRouter()
const matchingStore = useMatchingStore()

const title = ref('')
const textContent = ref('')
const submitting = ref(false)
const selectedFile = ref<File | null>(null)
const uploadRef = ref()
const activeTab = ref('text')
const titleAutoFilled = ref(false) // 标记需求名称是否是从文件名自动填充的

const createdRequirements = ref<RequirementItem[]>([])
const currentRequirementId = ref<string | null>(null)
const parsingError = ref<string | null>(null)

// Computed
const previewText = computed(() => {
  return textContent.value
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)
})

const previewLines = computed(() => previewText.value.length)

const canSubmit = computed(() => {
  const hasTitle = title.value.trim().length > 0
  const hasContent = (textContent.value.trim() && activeTab.value === 'text') ||
                     (selectedFile.value && activeTab.value === 'file')
  return hasTitle && hasContent
})

const submitButtonText = computed(() => {
  if (activeTab.value === 'text') {
    return '创建需求'
  } else {
    return '上传并解析'
  }
})

// Methods
function handleTitleInput() {
  // 用户手动修改需求名称，取消自动填充标记
  if (titleAutoFilled.value) {
    titleAutoFilled.value = false
  }
}

function handleTextChange() {
  if (textContent.value.trim()) {
    selectedFile.value = null
    uploadRef.value?.clearFiles()
  }
}

function handleFileChange(file: UploadFile) {
  if (file.raw) {
    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024 // 10MB in bytes
    if (file.raw.size > maxSize) {
      parsingError.value = `文件过大！

文件名: ${file.name}
文件大小: ${formatFileSize(file.raw.size)}
最大限制: 10 MB

请压缩文件或选择其他文件。`
      ElMessage.error('文件大小超过 10MB 限制')
      // Clear the file
      uploadRef.value?.clearFiles()
      selectedFile.value = null
      return
    }

    // Clear any previous errors
    parsingError.value = null

    selectedFile.value = file.raw
    textContent.value = ''

    // 如果需求名称为空，自动使用文件名（去除扩展名）作为需求名称
    if (!title.value.trim()) {
      const fileName = file.name
      const lastDotIndex = fileName.lastIndexOf('.')
      if (lastDotIndex > 0) {
        title.value = fileName.substring(0, lastDotIndex)
      } else {
        title.value = fileName
      }
      titleAutoFilled.value = true // 标记为自动填充
    } else {
      titleAutoFilled.value = false // 用户已手动输入，不是自动填充
    }
  }
}

function handleFileRemove() {
  selectedFile.value = null
  parsingError.value = null
  // 如果需求名称是从文件名自动填充的，删除文件时也清空需求名称
  if (titleAutoFilled.value) {
    title.value = ''
    titleAutoFilled.value = false
  }
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件')
}

async function handleSubmit() {
  // Clear any previous errors
  parsingError.value = null

  // 验证需求名称
  if (!title.value.trim()) {
    ElMessage.warning('请输入需求名称')
    return
  }

  if (!canSubmit.value) {
    ElMessage.warning('请输入需求文本或上传文件')
    return
  }

  submitting.value = true
  try {
    if (activeTab.value === 'text' && textContent.value.trim()) {
      // 文本提交
      const requirement = await matchingStore.createTextRequirement({
        title: title.value,
        requirement_text: textContent.value,
        created_by: 'admin'
      } as any)

      currentRequirementId.value = requirement.id
      createdRequirements.value = requirement.items || []

      ElMessage.success(`成功创建 ${requirement.items?.length || 0} 条需求`)
      // 清空标题和内容，准备下一次输入
      title.value = ''
      textContent.value = ''
    } else if (activeTab.value === 'file' && selectedFile.value) {
      // 文件上传
      try {
        const requirement = await matchingStore.uploadRequirement(
          selectedFile.value,
          'admin',
          title.value
        )

        currentRequirementId.value = requirement.id
        createdRequirements.value = requirement.items || []

        ElMessage.success(`成功解析 ${requirement.items?.length || 0} 条需求`)
        clearFile()
        // 清空标题，准备下一次输入
        title.value = ''
      } catch (fileError: any) {
        // Extract detailed error message
        const errorMsg = fileError.response?.data?.error || fileError.message || '文件解析失败'

        // Show detailed parsing error in UI
        parsingError.value = `${errorMsg}

文件名: ${selectedFile.value?.name}
文件大小: ${selectedFile.value ? formatFileSize(selectedFile.value.size) : 'N/A'}

请检查：
1. 文件格式是否正确（支持 .xlsx, .xls, .csv, .docx）
2. 文件是否损坏
3. 文件内容是否包含有效的需求数据
4. 文件大小是否超过 10MB`

        ElMessage.error('文件解析失败，请查看下方错误详情')
        throw fileError
      }
    }
  } catch (error: any) {
    // Error already handled above for file upload
    if (activeTab.value === 'text') {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

function handleClear() {
  ElMessageBox.confirm(
    '确定要清空所有内容吗？',
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    handleReset()
    ElMessage.success('已清空')
  }).catch(() => {
    // 用户取消
  })
}

function handleReset() {
  title.value = ''
  textContent.value = ''
  createdRequirements.value = []
  currentRequirementId.value = null
  parsingError.value = null
  clearFile()
}

function clearFile() {
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function getFileType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const types: Record<string, string> = {
    'xlsx': 'Excel 文件',
    'xls': 'Excel 文件',
    'csv': 'CSV 文件',
    'docx': 'Word 文档'
  }
  return types[ext || ''] || '未知类型'
}

function handleGoToMatching() {
  if (currentRequirementId.value) {
    router.push(`/matching/results/${currentRequirementId.value}`)
  }
}
</script>

<style scoped lang="scss">
.requirement-create {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.upload-demo {
  width: 100%;
}

:deep(.el-upload-dragger) {
  padding: 40px;
}

:deep(.el-icon--upload) {
  font-size: 67px;
  color: var(--el-text-color-secondary);
  margin-bottom: 16px;
}

.file-info {
  margin-top: 20px;
}

.button-group {
  display: flex;
  gap: 10px;
}

.preview-content {
  max-height: 300px;
  overflow-y: auto;
  background: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 4px;
}

.preview-line {
  padding: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);

  &:last-child {
    border-bottom: none;
  }
}

.mr-10 {
  margin-right: 10px;
}

.mb-20 {
  margin-bottom: 20px;
}

.mt-20 {
  margin-top: 20px;
}

.text-center {
  text-align: center;
}
</style>
