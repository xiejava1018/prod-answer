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

        <!-- Auto Analysis Option -->
        <el-form-item label="自动分析">
          <el-switch v-model="autoAnalyze" active-text="提交后自动开始匹配分析" />
          <div class="form-tip">
            开启后将在创建需求时自动进行匹配分析，完成后直接跳转到结果页面
          </div>
        </el-form-item>

        <!-- Submit Buttons -->
        <el-form-item>
          <div class="button-group">
            <el-button
              type="primary"
              size="large"
              @click="handleSubmit"
              :loading="submitting || analyzing"
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

    <!-- Progress Indicator -->
    <el-card v-if="submitting || analyzing" class="mt-20 progress-card">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon class="is-loading"><Loading /></el-icon>
            处理进度
          </span>
          <el-tag v-if="currentStep" :type="getStepType(currentStep)">
            {{ getStepText(currentStep) }}
          </el-tag>
        </div>
      </template>

      <!-- Progress Steps -->
      <el-steps :active="activeStep" finish-status="success" align-center class="mb-20">
        <el-step title="上传文件" />
        <el-step title="解析需求" />
        <el-step title="匹配分析" />
        <el-step title="完成" />
      </el-steps>

      <!-- Progress Bar -->
      <div class="progress-section">
        <div class="progress-info">
          <span>{{ progressMessage }}</span>
          <el-tag>{{ progressPercent }}%</el-tag>
        </div>
        <el-progress
          :percentage="progressPercent"
          :status="progressStatus"
          :stroke-width="20"
          :text-inside="true"
        />
      </div>

      <!-- Task Status Details -->
      <div v-if="taskId" class="task-details">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="任务ID">
            <el-text type="info">{{ taskId }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item label="分析模式">
            LLM 增强分析
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

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
  Plus,
  Loading
} from '@element-plus/icons-vue'
import type { RequirementItem } from '@/types'

const router = useRouter()
const matchingStore = useMatchingStore()

const title = ref('')
const textContent = ref('')
const submitting = ref(false)
const analyzing = ref(false)  // 分析进行中
const selectedFile = ref<File | null>(null)
const uploadRef = ref()
const activeTab = ref('text')
const titleAutoFilled = ref(false) // 标记需求名称是否是从文件名自动填充的
const autoAnalyze = ref(true)  // 默认开启自动分析

// Progress state
const currentStep = ref(0)  // 0: 上传, 1: 解析, 2: 分析, 3: 完成
const progressMessage = ref('')
const progressPercent = ref(0)
const taskId = ref<string>('')

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

// Progress status
const progressStatus = computed(() => {
  if (analyzing.value) return 'warning'
  if (progressPercent.value === 100) return 'success'
  return ''
})

// Active step for progress indicator
const activeStep = computed(() => {
  if (submitting.value && currentStep.value === 0) return 0
  if (analyzing.value) return 2
  if (progressPercent.value === 100) return 3
  return currentStep.value
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

  // Reset progress
  currentStep.value = 0
  progressPercent.value = 0
  taskId.value = ''

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
    let requirementId: string

    if (activeTab.value === 'text' && textContent.value.trim()) {
      // 文本提交 - 步骤1: 上传
      updateProgress(0, '正在创建需求...', 30)

      const requirement = await matchingStore.createTextRequirement({
        title: title.value,
        requirement_text: textContent.value,
        created_by: 'admin'
      }, autoAnalyze.value)  // 传递自动分析选项

      requirementId = requirement.id
      currentRequirementId.value = requirement.id
      createdRequirements.value = requirement.items || []

      // 步骤2: 解析完成
      updateProgress(1, `成功创建 ${requirement.items?.length || 0} 条需求`, 100)

      // 清空标题和内容，准备下一次输入
      title.value = ''
      textContent.value = ''

      // 如果不自动分析，在这里停止
      if (!autoAnalyze.value) {
        ElMessage.success('需求创建成功！')
        submitting.value = false
        return
      }

    } else if (activeTab.value === 'file' && selectedFile.value) {
      // 文件上传 - 步骤1: 上传
      updateProgress(0, '正在上传文件...', 20)

      try {
        const requirement = await matchingStore.uploadRequirement(
          selectedFile.value,
          'admin',
          title.value,
          autoAnalyze.value  // 传递自动分析选项
        )

        // 步骤2: 解析
        updateProgress(1, `正在解析文件... (已识别 ${requirement.items?.length || 0} 条需求)`, 80)

        requirementId = requirement.id
        currentRequirementId.value = requirement.id
        createdRequirements.value = requirement.items || []

        clearFile()
        // 清空标题，准备下一次输入
        title.value = ''

        // 如果不自动分析，在这里停止
        if (!autoAnalyze.value) {
          updateProgress(3, '解析完成！', 100)
          ElMessage.success(`成功解析 ${requirement.items?.length || 0} 条需求`)
          submitting.value = false
          setTimeout(() => {
            // Reset progress after 2 seconds
            currentStep.value = 0
            progressPercent.value = 0
          }, 2000)
          return
        }

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
        submitting.value = false
        throw fileError
      }
    }

    // Auto-start matching analysis if enabled
    if (autoAnalyze.value && requirementId) {
      await handleAutoAnalysis(requirementId)
    }
  } catch (error: any) {
    // Error already handled above for file upload
    if (activeTab.value === 'text') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// Auto-start matching analysis
async function handleAutoAnalysis(requirementId: string) {
  analyzing.value = true

  try {
    // 步骤3: 开始分析
    updateProgress(2, '正在启动LLM增强匹配分析...', 0)

    // Start async analysis
    const taskResponse = await matchingStore.analyzeAsync(
      requirementId,
      0.75,  // threshold
      undefined,  // llm_config_id (use default)
      'full'  // llm_analysis_mode
    )

    taskId.value = taskResponse.task_id
    updateProgress(2, `LLM分析已启动（任务ID: ${taskResponse.task_id}）`, 0)

    // Poll for completion with real-time progress updates
    const result = await matchingStore.pollTaskStatus(
      taskResponse.task_id,
      120,  // max attempts
      1000,  // interval (1 second)
      (progress, status) => {
        // Update progress based on actual backend progress
        if (progress < 30) {
          updateProgress(2, `正在进行向量匹配... ${progress}%`, progress)
        } else if (progress < 90) {
          updateProgress(2, `正在进行LLM增强分析... ${progress}%`, progress)
        } else {
          updateProgress(2, `正在完成最后处理... ${progress}%`, progress)
        }
      }
    )

    // Update to 100% when complete
    updateProgress(3, '分析完成！正在跳转...', 100)

    // Show success message and navigate to results
    const matchCount = result.total_matches || 0
    const itemCount = result.total_items || 0
    const llmTime = result.llm_analysis_time?.toFixed(1) || 'N/A'

    ElMessage.success({
      message: `🎉 匹配分析完成！共 ${itemCount} 个需求项，匹配到 ${matchCount} 个结果（LLM耗时: ${llmTime}秒）`,
      duration: 2000,
      onClose: () => {
        // Navigate to results page
        router.push(`/matching/results/${requirementId}`)
      }
    })

  } catch (error: any) {
    console.error('Auto analysis error:', error)
    ElMessage.error(error.response?.data?.error || error.message || '自动匹配分析失败')

    // Reset progress
    currentStep.value = 0
    progressPercent.value = 0
    taskId.value = ''

    // Even if auto analysis failed, still offer option to view results
    ElMessage.info('您可以稍后手动前往匹配分析页面查看结果')
  } finally {
    submitting.value = false
    analyzing.value = false
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

// Progress helper functions
function getStepType(step: number): string {
  if (step === activeStep.value) return 'primary'
  if (step < activeStep.value) return 'success'
  return 'info'
}

function getStepText(step: number): string {
  const steps = ['上传中', '解析中', '分析中', '已完成']
  return steps[step] || ''
}

function updateProgress(step: number, message: string, percent: number) {
  currentStep.value = step
  progressMessage.value = message
  progressPercent.value = Math.round(percent)  // Ensure integer value
  console.log(`[Progress Update] Step: ${step}, Message: ${message}, Percent: ${progressPercent.value}%`)
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

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.progress-card {
  border: 2px solid var(--el-color-primary);
  background: var(--el-fill-color-blur);
}

.progress-section {
  margin-top: 20px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 600;
}

.task-details {
  margin-top: 20px;
}

:deep(.el-progress-bar__inner) {
  transition: all 0.3s ease;
}

:deep(.el-step__title) {
  font-size: 14px;
}
</style>
