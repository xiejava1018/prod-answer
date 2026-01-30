<template>
  <div class="llm-config-container">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <h2>LLM模型配置管理</h2>
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加配置
          </el-button>
        </div>
      </template>

      <!-- Filter Bar -->
      <div class="filter-bar">
        <el-select
          v-model="filters.provider"
          placeholder="选择提供商"
          clearable
          @change="loadConfigs"
          style="width: 200px"
        >
          <el-option label="OpenAI" value="openai" />
          <el-option label="ZhipuAI" value="zhipuai" />
          <el-option label="Qwen" value="qwen" />
          <el-option label="SiliconFlow" value="siliconflow" />
        </el-select>

        <el-select
          v-model="filters.is_active"
          placeholder="状态"
          clearable
          @change="loadConfigs"
          style="width: 150px"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>

        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <!-- Config List -->
    <el-card class="table-card">
      <el-table :data="configs" v-loading="loading" stripe>
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag :type="getProviderTagType(row.provider)">
              {{ getProviderLabel(row.provider) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="model_name" label="模型名称" width="200" />

        <el-table-column prop="base_url" label="API地址" show-overflow-tooltip />

        <el-table-column prop="max_tokens" label="最大Token" width="120" align="center" />

        <el-table-column prop="temperature" label="温度" width="100" align="center" />

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="toggleActive(row)"
              :loading="row.toggling"
            />
          </template>
        </el-table-column>

        <el-table-column label="默认" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            <el-button
              v-else
              link
              type="primary"
              size="small"
              @click="setDefaultConfig(row)"
            >
              设为默认
            </el-button>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="testConnection(row)" :loading="row.testing">
              <el-icon><Connection /></el-icon>
              测试连接
            </el-button>
            <el-button link type="primary" @click="editConfig(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button link type="danger" @click="deleteConfig(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑LLM配置' : '添加LLM配置'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" placeholder="选择提供商" style="width: 100%" @change="handleProviderChange">
            <el-option label="OpenAI" value="openai" />
            <el-option label="ZhipuAI" value="zhipuai" />
            <el-option label="Qwen" value="qwen" />
            <el-option label="SiliconFlow" value="siliconflow" />
          </el-select>
        </el-form-item>

        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="例如: gpt-4o-mini" />
          <div class="form-tip" v-if="form.provider === 'openai'">
            推荐: gpt-4o-mini (性价比高) 或 gpt-4o (性能更强)
          </div>
          <div class="form-tip" v-else-if="form.provider === 'zhipuai'">
            推荐: glm-4-flash (免费) 或 glm-4-plus (性能更强)
          </div>
          <div class="form-tip" v-else-if="form.provider === 'qwen'">
            推荐: qwen-plus (性价比高) 或 qwen-max (性能更强)
          </div>
          <div class="form-tip" v-else-if="form.provider === 'siliconflow'">
            推荐: Qwen/Qwen2.5-7B-Instruct 或其他开源模型
          </div>
        </el-form-item>

        <el-form-item label="API地址" prop="base_url">
          <el-input v-model="form.base_url" placeholder="自动填充或手动输入" />
          <div class="form-tip" v-if="form.provider === 'openai'">
            留空使用默认地址 https://api.openai.com/v1
          </div>
          <div class="form-tip" v-else-if="form.provider !== 'openai' && form.base_url">
            已自动填充推荐地址，可按需修改
          </div>
        </el-form-item>

        <el-form-item label="API密钥" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            placeholder="输入API密钥"
          />
        </el-form-item>

        <el-form-item label="最大Token" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="1" :max="100000" style="width: 100%" />
          <div class="form-tip">已根据模型自动设置推荐值</div>
        </el-form-item>

        <el-form-item label="温度" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
          <div class="form-tip">0.0-2.0，值越高输出越随机，0.7为推荐值</div>
        </el-form-item>

        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>

        <el-form-item label="设为默认" prop="is_default">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Edit, Delete, Connection } from '@element-plus/icons-vue'
import { llmConfigApi, type LLMModelConfig } from '@/api/llm'

// Data
const configs = ref<LLMModelConfig[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const filters = reactive({
  provider: '',
  is_active: undefined as boolean | undefined
})

const form = reactive({
  id: '',
  provider: 'openai',
  model_name: '',
  base_url: '',
  api_key: '',
  max_tokens: 4096,
  temperature: 0.7,
  is_active: true,
  is_default: false
})

// Validation rules
const rules: FormRules = {
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  api_key: [
    {
      required: true,
      message: '请输入API密钥',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (!value || value.trim() === '') {
          callback(new Error('请输入API密钥'))
        } else {
          callback()
        }
      }
    }
  ],
  max_tokens: [{ required: true, message: '请输入最大Token数', trigger: 'blur' }]
}

// Methods
const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await llmConfigApi.list(filters)
    configs.value = (response.results || response.providers || []).map((config: LLMModelConfig) => ({
      ...config,
      testing: false,
      toggling: false
    }))
  } catch (error: any) {
    console.error('Load configs error:', error)
    ElMessage.error(error.response?.data?.error || '加载配置失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  // 重置表单并设置默认值
  resetForm()
  // 触发一次提供商联动以设置初始值
  handleProviderChange()
  dialogVisible.value = true
}

const editConfig = (row: LLMModelConfig) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    provider: row.provider,
    model_name: row.model_name,
    base_url: row.base_url || '',
    api_key: '', // Don't pre-fill API key for security
    max_tokens: row.max_tokens,
    temperature: row.temperature,
    is_active: row.is_active,
    is_default: row.is_default
  })
  dialogVisible.value = true
}

const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(form, {
    id: '',
    provider: 'openai',
    model_name: 'gpt-4o-mini',
    base_url: '',
    api_key: '',
    max_tokens: 4096,
    temperature: 0.7,
    is_active: true,
    is_default: false
  })
}

const handleProviderChange = () => {
  const provider = form.provider

  // 根据提供商自动配置模型名称和API地址
  if (provider === 'openai') {
    form.model_name = 'gpt-4o-mini'
    form.base_url = ''
    form.max_tokens = 4096
    form.temperature = 0.7
  } else if (provider === 'zhipuai') {
    form.model_name = 'glm-4-flash'
    form.base_url = 'https://open.bigmodel.cn/api/paas/v4'
    form.max_tokens = 8192
    form.temperature = 0.7
  } else if (provider === 'qwen') {
    form.model_name = 'qwen-plus'
    form.base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    form.max_tokens = 8192
    form.temperature = 0.7
  } else if (provider === 'siliconflow') {
    form.model_name = 'Qwen/Qwen2.5-7B-Instruct'
    form.base_url = 'https://api.siliconflow.cn/v1'
    form.max_tokens = 4096
    form.temperature = 0.7
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 检查重复配置（只在创建模式下）
    if (!isEdit.value) {
      const duplicate = configs.value.find(
        c => c.provider === form.provider && c.model_name === form.model_name
      )
      if (duplicate) {
        ElMessage.error(
          `该配置已存在：${getProviderLabel(form.provider)} - ${form.model_name}`
        )
        return
      }
    }

    submitting.value = true
    try {
      const payload: any = {
        provider: form.provider,
        model_name: form.model_name,
        base_url: form.base_url || '',
        api_key_encrypted: form.api_key,
        max_tokens: form.max_tokens,
        temperature: form.temperature,
        is_active: form.is_active,
        is_default: form.is_default
      }

      // 只在编辑模式且未修改密钥时才不发送api_key
      if (isEdit.value && !form.api_key) {
        delete payload.api_key_encrypted
      }

      console.log('Submitting payload:', JSON.stringify(payload, null, 2))

      if (isEdit.value) {
        await llmConfigApi.update(form.id, payload)
        ElMessage.success('配置更新成功')
      } else {
        await llmConfigApi.create(payload)
        ElMessage.success('配置创建成功')
      }

      dialogVisible.value = false
      loadConfigs()
    } catch (error: any) {
      console.error('Submit error:', error)
      console.error('Error response data:', error.response?.data)

      // 显示详细的错误信息
      const errorMsg = error.response?.data
        ? (typeof error.response.data === 'string'
          ? error.response.data
          : JSON.stringify(error.response.data))
        : (error.message || '操作失败')

      ElMessage.error('创建失败: ' + errorMsg)
    } finally {
      submitting.value = false
    }
  })
}

const testConnection = async (row: any) => {
  row.testing = true
  try {
    const result = await llmConfigApi.test(row.id)
    if (result.is_connected) {
      ElMessage.success(`连接成功！响应时间: ${result.response_time_ms}ms`)
    } else {
      ElMessage.error(result.error || '连接失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.error || '连接测试失败')
  } finally {
    row.testing = false
  }
}

const toggleActive = async (row: any) => {
  row.toggling = true
  try {
    await llmConfigApi.partialUpdate(row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error: any) {
    // Revert on error
    row.is_active = !row.is_active
    ElMessage.error('状态更新失败')
  } finally {
    row.toggling = false
  }
}

const setDefaultConfig = async (row: LLMModelConfig) => {
  try {
    await llmConfigApi.setDefault(row.id)
    ElMessage.success(`${row.model_name} 已设为默认配置`)
    loadConfigs()
  } catch (error: any) {
    ElMessage.error('设置失败')
  }
}

const deleteConfig = async (row: LLMModelConfig) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除配置 "${row.model_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await llmConfigApi.delete(row.id)
    ElMessage.success('删除成功')
    loadConfigs()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetFilters = () => {
  filters.provider = ''
  filters.is_active = undefined
  loadConfigs()
}

// Helper functions
const getProviderLabel = (provider: string) => {
  const labels: Record<string, string> = {
    openai: 'OpenAI',
    zhipuai: 'ZhipuAI',
    qwen: 'Qwen',
    siliconflow: 'SiliconFlow'
  }
  return labels[provider] || provider
}

const getProviderTagType = (provider: string) => {
  const types: Record<string, any> = {
    openai: 'success',
    zhipuai: 'warning',
    qwen: 'info',
    siliconflow: 'primary'
  }
  return types[provider] || ''
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// Lifecycle
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.llm-config-container {
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

.filter-bar {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.table-card {
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
