<template>
  <div class="embedding-settings">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        Embedding模型配置
      </template>
    </el-page-header>

    <el-row :gutter="20">
      <!-- Config List -->
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>模型配置列表</span>
              <el-button type="primary" @click="showAddDialog">
                <el-icon><Plus /></el-icon>
                添加配置
              </el-button>
            </div>
          </template>

          <el-table :data="configs" v-loading="loading" border>
            <el-table-column prop="model_name" label="模型名称" width="200" />
            <el-table-column prop="model_type_display" label="类型" width="220">
              <template #default="{ row }">
                <el-tag>{{ row.model_type_display || row.model_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="provider_name_display" label="提供商" width="180">
              <template #default="{ row }">
                <el-tag v-if="row.provider_name_display" type="info">
                  {{ row.provider_name_display }}
                </el-tag>
                <span v-else>{{ row.provider }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="dimension" label="维度" width="100" />
            <el-table-column label="API密钥" width="100">
              <template #default="{ row }">
                <el-tag :type="row.has_api_key ? 'success' : 'warning'" size="small">
                  {{ row.has_api_key ? '已配置' : '未配置' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success">默认</el-tag>
                <el-tag v-else-if="row.is_active" type="info">活跃</el-tag>
                <el-tag v-else type="warning">禁用</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  @click="handleTestConnection(row)"
                  :loading="testing === row.id"
                  :disabled="!row.is_active"
                  size="small"
                >
                  测试连接
                </el-button>
                <el-button
                  link
                  type="success"
                  @click="handleSetDefault(row)"
                  :disabled="row.is_default"
                  size="small"
                >
                  设为默认
                </el-button>
                <el-button link type="primary" @click="handleEdit(row)" size="small">
                  编辑
                </el-button>
                <el-button link type="danger" @click="handleDelete(row)" size="small">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- System Status -->
      <el-col :span="8">
        <el-card class="mb-20">
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
            </div>
          </template>

          <div class="status-list">
            <div class="status-item">
              <span class="status-label">默认模型:</span>
              <el-tag type="success">{{ defaultModel || '未配置' }}</el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">活跃配置:</span>
              <el-tag type="info">{{ activeConfigsCount }}</el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">总配置数:</span>
              <el-tag type="info">{{ configs.length }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速配置指南</span>
            </div>
          </template>

          <el-collapse>
            <el-collapse-item title="硅基流动 SiliconFlow (推荐)" name="siliconflow">
              <div class="guide-content">
                <p><strong>免费额度，推荐使用</strong></p>
                <ol class="guide-steps">
                  <li>访问 <el-link href="https://siliconflow.cn/" target="_blank">siliconflow.cn</el-link></li>
                  <li>注册并创建API密钥</li>
                  <li>选择 "OpenAI-Compatible" 类型</li>
                  <li>提供商选择 "硅基流动 SiliconFlow"</li>
                  <li>填入API密钥即可</li>
                </ol>
              </div>
            </el-collapse-item>

            <el-collapse-item title="智谱AI ZhipuAI" name="zhipuai">
              <div class="guide-content">
                <p><strong>国产大模型，稳定可靠</strong></p>
                <ol class="guide-steps">
                  <li>访问 <el-link href="https://open.bigmodel.cn/" target="_blank">open.bigmodel.cn</el-link></li>
                  <li>注册并获取API密钥</li>
                  <li>选择 "OpenAI-Compatible" 类型</li>
                  <li>提供商选择 "智谱AI ZhipuAI"</li>
                  <li>填入API密钥即可</li>
                </ol>
              </div>
            </el-collapse-item>

            <el-collapse-item title="OpenAI官方" name="openai">
              <div class="guide-content">
                <p><strong>原版OpenAI API</strong></p>
                <ol class="guide-steps">
                  <li>获取 OpenAI API Key</li>
                  <li>选择 "OpenAI" 类型</li>
                  <li>填入API密钥</li>
                  <li>模型会自动选择 text-embedding-3-small</li>
                </ol>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>

    <!-- Add/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑配置' : '添加配置'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="140px"
      >
        <el-form-item label="模型名称" prop="model_name">
          <el-input
            v-model="formData.model_name"
            placeholder="例如: siliconflow-bge-zh"
            :disabled="isEdit"
          />
          <div class="form-tip">
            唯一标识，创建后不可修改
          </div>
        </el-form-item>

        <el-form-item label="模型类型" prop="model_type">
          <el-select
            v-model="formData.model_type"
            placeholder="请选择类型"
            @change="handleTypeChange"
            style="width: 100%"
          >
            <el-option label="OpenAI-Compatible (硅基流动/智谱/通义等)" value="openai-compatible" />
            <el-option label="OpenAI官方" value="openai" />
            <el-option label="本地Sentence-Transformers" value="sentence-transformers" />
          </el-select>
          <div class="form-tip">
            支持国产API和OpenAI兼容接口
          </div>
        </el-form-item>

        <!-- OpenAI-Compatible Configuration -->
        <template v-if="formData.model_type === 'openai-compatible'">
          <el-form-item label="API提供商" prop="provider_name">
            <el-select
              v-model="formData.provider_name"
              placeholder="请选择API提供商"
              @change="handleProviderChange"
              style="width: 100%"
            >
              <el-option label="硅基流动 SiliconFlow (推荐)" value="siliconflow" />
              <el-option label="智谱AI ZhipuAI" value="zhipuai" />
              <el-option label="阿里通义千问 Qwen" value="qwen" />
              <el-option label="其他OpenAI兼容API" value="other" />
            </el-select>
          </el-form-item>

          <el-form-item label="API基础URL" prop="base_url">
            <el-input
              v-model="formData.base_url"
              placeholder="例如: https://api.siliconflow.cn/v1"
            />
            <div class="form-tip">
              OpenAI兼容API的基础URL
            </div>
          </el-form-item>

          <el-form-item label="API密钥" prop="api_key_encrypted">
            <el-input
              v-model="formData.api_key_encrypted"
              type="password"
              placeholder="sk-..."
              show-password
            />
            <div class="form-tip">
              API密钥会加密存储
            </div>
          </el-form-item>

          <el-form-item label="向量维度" prop="dimension">
            <el-input-number v-model="formData.dimension" :min="1" :max="4096" style="width: 100%" />
            <div class="form-tip">
              BGE-large: 1024, 智谱embedding-2: 1024, 通义v3: 1536
            </div>
          </el-form-item>

          <el-form-item label="模型名称">
            <el-input
              v-model="modelParams.model"
              placeholder="例如: BAAI/bge-large-zh-v1.5"
            />
            <div class="form-tip">
              模型参数中的model字段
            </div>
          </el-form-item>
        </template>

        <!-- OpenAI Configuration -->
        <template v-if="formData.model_type === 'openai'">
          <el-form-item label="提供商">
            <el-input v-model="formData.provider" disabled />
          </el-form-item>

          <el-form-item label="API密钥" prop="api_key_encrypted">
            <el-input
              v-model="formData.api_key_encrypted"
              type="password"
              placeholder="sk-..."
              show-password
            />
          </el-form-item>

          <el-form-item label="API端点">
            <el-input
              v-model="formData.api_endpoint"
              placeholder="https://api.openai.com/v1 (可选)"
            />
          </el-form-item>

          <el-form-item label="向量维度" prop="dimension">
            <el-input-number v-model="formData.dimension" :min="1" style="width: 100%" />
            <div class="form-tip">
              text-embedding-3-small: 1536, text-embedding-3-large: 3072
            </div>
          </el-form-item>
        </template>

        <!-- Sentence-Transformers Configuration -->
        <template v-if="formData.model_type === 'sentence-transformers'">
          <el-form-item label="提供商">
            <el-input v-model="formData.provider" disabled />
          </el-form-item>

          <el-form-item label="模型路径" prop="model_path">
            <el-input
              v-model="modelParams.model_path"
              placeholder="例如: all-MiniLM-L6-v2"
            />
            <div class="form-tip">
              首次使用会自动下载模型
            </div>
          </el-form-item>

          <el-form-item label="向量维度" prop="dimension">
            <el-input-number v-model="formData.dimension" :min="1" style="width: 100%" />
            <div class="form-tip">
              MiniLM: 384, MPNet: 768, BGE-base: 768
            </div>
          </el-form-item>
        </template>

        <el-form-item label="状态">
          <el-checkbox v-model="formData.is_active">启用此配置</el-checkbox>
          <el-checkbox v-model="formData.is_default" class="ml-20">设为默认</el-checkbox>
          <div class="form-tip">
            默认配置将用于所有Embedding操作
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useEmbeddingStore } from '@/store'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { EmbeddingModelConfig } from '@/types'

const embeddingStore = useEmbeddingStore()

const loading = ref(false)
const testing = ref<string | null>(null)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const formRef = ref<FormInstance>()

const configs = computed(() => embeddingStore.configs)
const defaultModel = computed(() => embeddingStore.defaultConfig?.model_name || '')
const activeConfigsCount = computed(() => configs.value.filter(c => c.is_active).length)

const formData = ref<Partial<EmbeddingModelConfig>>({
  model_name: '',
  model_type: 'openai-compatible',
  provider: 'openai-compatible',
  provider_name: 'siliconflow',
  base_url: 'https://api.siliconflow.cn/v1',
  api_endpoint: '',
  api_key_encrypted: '',
  dimension: 1024,
  is_active: true,
  is_default: false,
  model_params: {}
})

const modelParams = reactive<{
  model?: string
  model_path?: string
}>({})

const editingId = ref<string | null>(null)

const formRules: FormRules = {
  model_name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  model_type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  provider_name: [
    { required: true, message: '请选择API提供商', trigger: 'change' }
  ],
  base_url: [
    { required: true, message: '请输入API基础URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ],
  api_key_encrypted: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ],
  dimension: [
    { required: true, message: '请输入向量维度', trigger: 'blur' }
  ]
}

onMounted(async () => {
  await loadConfigs()
  await loadDefaultConfig()
})

async function loadConfigs() {
  loading.value = true
  try {
    await embeddingStore.fetchConfigs()
  } finally {
    loading.value = false
  }
}

async function loadDefaultConfig() {
  await embeddingStore.fetchDefaultConfig()
}

function showAddDialog() {
  isEdit.value = false
  editingId.value = null
  modelParams.model = ''
  modelParams.model_path = 'all-MiniLM-L6-v2'

  formData.value = {
    model_name: '',
    model_type: 'openai-compatible',
    provider: 'openai-compatible',
    provider_name: 'siliconflow',
    base_url: 'https://api.siliconflow.cn/v1',
    api_endpoint: '',
    api_key_encrypted: '',
    dimension: 1024,
    is_active: true,
    is_default: false,
    model_params: {}
  }
  dialogVisible.value = true
}

function handleEdit(row: EmbeddingModelConfig) {
  isEdit.value = true
  editingId.value = row.id

  // Load model params
  if (row.model_params?.model) {
    modelParams.model = row.model_params.model
  }
  if (row.model_params?.model_path) {
    modelParams.model_path = row.model_params.model_path
  }

  formData.value = { ...row }

  // Ensure api_key is populated (but not shown to user)
  if (!formData.value.api_key_encrypted) {
    formData.value.api_key_encrypted = ''
  }

  dialogVisible.value = true
}

function handleTypeChange() {
  const type = formData.value.model_type

  if (type === 'openai-compatible') {
    formData.value.provider = 'openai-compatible'
    formData.value.provider_name = 'siliconflow'
    formData.value.base_url = 'https://api.siliconflow.cn/v1'
    formData.value.dimension = 1024
    modelParams.model = 'BAAI/bge-large-zh-v1.5'
  } else if (type === 'openai') {
    formData.value.provider = 'openai'
    formData.value.dimension = 1536
  } else if (type === 'sentence-transformers') {
    formData.value.provider = 'sentence-transformers'
    formData.value.dimension = 384
    modelParams.model_path = 'all-MiniLM-L6-v2'
  }
}

function handleProviderChange() {
  const provider = formData.value.provider_name

  if (provider === 'siliconflow') {
    formData.value.base_url = 'https://api.siliconflow.cn/v1'
    formData.value.dimension = 1024
    modelParams.model = 'BAAI/bge-large-zh-v1.5'
  } else if (provider === 'zhipuai') {
    formData.value.base_url = 'https://open.bigmodel.cn/api/paas/v4'
    formData.value.dimension = 1024
    modelParams.model = 'embedding-2'
  } else if (provider === 'qwen') {
    formData.value.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    formData.value.dimension = 1536
    modelParams.model = 'text-embedding-v3'
  }
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    // Prepare model params
    const params: any = {}
    if (formData.value.model_type === 'openai-compatible') {
      params.model = modelParams.model || 'BAAI/bge-large-zh-v1.5'
    } else if (formData.value.model_type === 'openai') {
      params.model = formData.value.model_name?.includes('3-large')
        ? 'text-embedding-3-large'
        : 'text-embedding-3-small'
    } else if (formData.value.model_type === 'sentence-transformers') {
      params.model_path = modelParams.model_path || 'all-MiniLM-L6-v2'
    }

    const data = {
      ...formData.value,
      model_params: params,
      // Map provider_name to provider field
      provider: formData.value.provider_name || formData.value.provider
    }

    if (isEdit.value && editingId.value) {
      await embeddingStore.updateConfig(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await embeddingStore.createConfig(data)
      ElMessage.success('添加成功')
    }

    dialogVisible.value = false
    await loadConfigs()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? '更新失败: ' + error.message : '添加失败: ' + error.message)
    }
  } finally {
    submitting.value = false
  }
}

async function handleTestConnection(row: EmbeddingModelConfig) {
  testing.value = row.id
  try {
    const result = await embeddingStore.testConnection(row.id)
    if (result.is_connected) {
      ElMessage.success('✅ 连接测试成功！')
    } else {
      ElMessage.error('❌ 连接测试失败: ' + (result.error || '未知错误'))
    }
  } catch (error: any) {
    ElMessage.error('❌ 连接测试失败: ' + error.message)
  } finally {
    testing.value = null
  }
}

async function handleSetDefault(row: EmbeddingModelConfig) {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${row.model_name}" 设为默认模型吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await embeddingStore.setDefault(row.id)
    ElMessage.success('设置成功')
    await loadConfigs()
    await loadDefaultConfig()
  } catch (error) {
    // User cancelled
  }
}

async function handleDelete(row: EmbeddingModelConfig) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${row.model_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await embeddingStore.deleteConfig(row.id)
    ElMessage.success('删除成功')
    await loadConfigs()
    await loadDefaultConfig()
  } catch (error) {
    // User cancelled
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

.status-list {
  .status-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);

    &:last-child {
      border-bottom: none;
    }

    .status-label {
      font-weight: 500;
    }
  }
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

.ml-20 {
  margin-left: 20px;
}

.guide-content {
  font-size: 14px;

  p {
    margin: 0 0 8px 0;
    font-weight: 500;
  }

  .guide-steps {
    margin: 0;
    padding-left: 20px;

    li {
      margin-bottom: 6px;
      line-height: 1.5;
    }
  }
}
</style>
