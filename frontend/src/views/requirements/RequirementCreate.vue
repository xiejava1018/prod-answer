<template>
  <div class="requirement-create">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        创建能力需求
      </template>
    </el-page-header>

    <el-row :gutter="20">
      <!-- Text Input -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Document /></el-icon>
                文本输入
              </span>
            </div>
          </template>

          <el-form @submit.prevent="handleTextSubmit">
            <el-form-item label="需求名称">
              <el-input
                v-model="title"
                placeholder="请输入需求名称（可选）"
                clearable
              />
            </el-form-item>

            <el-form-item label="需求文本">
              <el-input
                v-model="textContent"
                type="textarea"
                :rows="10"
                placeholder="每行一个需求，例如：&#10;用户登录&#10;权限管理&#10;数据导出"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleTextSubmit"
                :loading="submitting"
                :disabled="!textContent.trim()"
              >
                <el-icon><Check /></el-icon>
                创建需求
              </el-button>
              <el-button @click="title = ''; textContent = ''">清空</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- File Upload -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Upload /></el-icon>
                文件上传
              </span>
            </div>
          </template>

          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            :on-exceed="handleExceed"
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

          <div class="mt-20" v-if="selectedFile">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="文件名">{{ selectedFile.name }}</el-descriptions-item>
              <el-descriptions-item label="文件大小">
                {{ formatFileSize(selectedFile.size) }}
              </el-descriptions-item>
              <el-descriptions-item label="文件类型">
                {{ selectedFile.type || '未知' }}
              </el-descriptions-item>
            </el-descriptions>

            <el-button
              type="primary"
              class="mt-20"
              @click="handleFileUpload"
              :loading="uploading"
            >
              <el-icon><Check /></el-icon>
              上传并解析
            </el-button>
            <el-button @click="clearFile">清除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Created Requirements -->
    <el-card v-if="createdRequirements.length > 0" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>已创建的需求</span>
          <el-tag>共 {{ createdRequirements.length }} 条</el-tag>
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
        <el-button @click="createdRequirements = []; currentRequirementId = null">
          创建更多需求
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMatchingStore } from '@/store'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadRawFile } from 'element-plus'
import {
  Document,
  Upload,
  Check,
  UploadFilled,
  Connection
} from '@element-plus/icons-vue'
import type { RequirementItem } from '@/types'

const router = useRouter()
const matchingStore = useMatchingStore()

const title = ref('')
const textContent = ref('')
const submitting = ref(false)
const uploading = ref(false)
const selectedFile = ref<File | null>(null)
const uploadRef = ref()

const createdRequirements = ref<RequirementItem[]>([])
const currentRequirementId = ref<string | null>(null)

async function handleTextSubmit() {
  if (!textContent.value.trim()) {
    ElMessage.warning('请输入需求文本')
    return
  }

  submitting.value = true
  try {
    const requirement = await matchingStore.createTextRequirement({
      title: title.value,
      requirement_text: textContent.value,
      created_by: 'admin'
    } as any)

    currentRequirementId.value = requirement.id
    createdRequirements.value = requirement.items || []

    ElMessage.success('需求创建成功')
    title.value = ''
    textContent.value = ''
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

function handleFileChange(file: UploadFile) {
  if (file.raw) {
    selectedFile.value = file.raw
  }
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件')
}

async function handleFileUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  try {
    const requirement = await matchingStore.uploadRequirement(
      selectedFile.value,
      'admin'
    )

    currentRequirementId.value = requirement.id
    createdRequirements.value = requirement.items || []

    ElMessage.success('文件上传并解析成功')
    clearFile()
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
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

function handleGoToMatching() {
  if (currentRequirementId.value) {
    router.push(`/matching/results/${currentRequirementId.value}`)
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
</style>
