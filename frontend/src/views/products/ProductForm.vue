<template>
  <div class="product-form">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑产品' : '创建产品' }}</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        v-loading="loading"
      >
        <el-form-item label="产品名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入产品名称" />
        </el-form-item>

        <el-form-item label="版本" prop="version">
          <el-input v-model="formData.version" placeholder="例如: 1.0.0" />
        </el-form-item>

        <el-form-item label="厂商" prop="vendor">
          <el-input v-model="formData.vendor" placeholder="请输入厂商名称" />
        </el-form-item>

        <el-form-item label="分类" prop="category">
          <el-select v-model="formData.category" placeholder="请选择分类" allow-create filterable>
            <el-option label="企业管理" value="企业管理" />
            <el-option label="办公软件" value="办公软件" />
            <el-option label="开发工具" value="开发工具" />
            <el-option label="云服务" value="云服务" />
            <el-option label="数据分析" value="数据分析" />
            <el-option label="人工智能" value="人工智能" />
          </el-select>
        </el-form-item>

        <el-form-item label="产品描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入产品描述"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Features Section (only for edit mode) -->
    <el-card v-if="isEdit && productId" class="mt-20">
      <template #header>
        <div class="card-header">
          <span>产品功能</span>
          <el-button type="primary" size="small" @click="showAddFeatureDialog">
            <el-icon><Plus /></el-icon>
            添加功能
          </el-button>
        </div>
      </template>

      <el-table :data="features" v-loading="featuresLoading" border style="width: 100%">
        <el-table-column prop="feature_name" label="功能名称" width="150" />
        <el-table-column prop="description" label="功能描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="subcategory" label="子分类" width="120" />
        <el-table-column prop="importance_level" label="重要性" width="150" align="center">
          <template #default="{ row }">
            <el-rate v-model="row.importance_level" disabled />
          </template>
        </el-table-column>
        <el-table-column label="向量状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(row as any).has_embedding ? 'success' : 'info'" size="small">
              {{ (row as any).has_embedding ? '已生成' : '未生成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleGenerateEmbedding(row)">
              生成向量
            </el-button>
            <el-button link type="danger" @click="handleDeleteFeature(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add Feature Dialog -->
    <el-dialog
      v-model="featureDialogVisible"
      title="添加功能"
      width="600px"
    >
      <el-form
        ref="featureFormRef"
        :model="featureFormData"
        :rules="featureFormRules"
        label-width="100px"
      >
        <el-form-item label="功能名称" prop="feature_name">
          <el-input v-model="featureFormData.feature_name" placeholder="请输入功能名称" />
        </el-form-item>

        <el-form-item label="功能描述" prop="description">
          <el-input
            v-model="featureFormData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入功能描述"
          />
        </el-form-item>

        <el-form-item label="分类" prop="category">
          <el-input v-model="featureFormData.category" placeholder="例如: 基础功能" />
        </el-form-item>

        <el-form-item label="子分类" prop="subcategory">
          <el-input v-model="featureFormData.subcategory" placeholder="例如: 用户管理" />
        </el-form-item>

        <el-form-item label="重要性" prop="importance_level">
          <el-rate v-model="featureFormData.importance_level" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="featureDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddFeature" :loading="addingFeature">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore } from '@/store'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { ProductFormData, FeatureFormData } from '@/types'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()

const formRef = ref<FormInstance>()
const featureFormRef = ref<FormInstance>()

const loading = ref(false)
const submitting = ref(false)
const featuresLoading = ref(false)
const addingFeature = ref(false)

const productId = computed(() => route.params.id as string)
const isEdit = computed(() => !!productId.value)

const formData = ref<ProductFormData>({
  name: '',
  version: '',
  vendor: '',
  category: '',
  description: ''
})

const featureFormData = ref<FeatureFormData>({
  feature_name: '',
  description: '',
  category: '',
  subcategory: '',
  importance_level: 5
})

const features = computed(() => productStore.features)

const featureDialogVisible = ref(false)

const formRules: FormRules = {
  name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' }
  ]
}

const featureFormRules: FormRules = {
  feature_name: [
    { required: true, message: '请输入功能名称', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入功能描述', trigger: 'blur' }
  ]
}

onMounted(async () => {
  if (isEdit.value) {
    await loadProduct()
    await loadFeatures()
  }
})

async function loadProduct() {
  loading.value = true
  try {
    await productStore.fetchProduct(productId.value)
    if (productStore.currentProduct) {
      formData.value = {
        name: productStore.currentProduct.name,
        version: productStore.currentProduct.version || '',
        vendor: productStore.currentProduct.vendor || '',
        category: productStore.currentProduct.category || '',
        description: productStore.currentProduct.description || ''
      }
    }
  } finally {
    loading.value = false
  }
}

async function loadFeatures() {
  featuresLoading.value = true
  try {
    await productStore.fetchFeatures(productId.value)
  } finally {
    featuresLoading.value = false
  }
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await productStore.updateProduct(productId.value, formData.value)
      ElMessage.success('更新成功')
    } else {
      const product = await productStore.createProduct(formData.value)
      ElMessage.success('创建成功')
      router.push(`/products/${product.id}`)
    }
  } catch (error: any) {
    if (error !== false) { // Not validation error
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  formRef.value?.resetFields()
}

function showAddFeatureDialog() {
  featureFormData.value = {
    feature_name: '',
    description: '',
    category: '',
    subcategory: '',
    importance_level: 5
  }
  featureDialogVisible.value = true
}

async function handleAddFeature() {
  if (!featureFormRef.value) return

  try {
    await featureFormRef.value.validate()
    addingFeature.value = true

    await productStore.addFeature(productId.value, featureFormData.value)
    ElMessage.success('添加成功')
    featureDialogVisible.value = false
    await loadFeatures()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error('添加失败')
    }
  } finally {
    addingFeature.value = false
  }
}

async function handleDeleteFeature(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除此功能吗？', '确认删除', {
      type: 'warning'
    })

    await productStore.deleteFeature(row.id)
    ElMessage.success('删除成功')
    await loadFeatures()
  } catch (error) {
    // User cancelled
  }
}

async function handleGenerateEmbedding(row: any) {
  try {
    const loading = ElLoading.service({ fullscreen: true })
    await productStore.generateFeatureEmbedding(row.id)
    loading.close()
    ElMessage.success('向量生成成功')
  } catch (error) {
    ElMessage.error('向量生成失败')
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
</style>
