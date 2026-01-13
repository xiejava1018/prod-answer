<template>
  <div class="product-detail">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        {{ product?.name || '产品详情' }}
      </template>
      <template #extra>
        <el-button type="primary" @click="$router.push(`/products/${productId}/edit`)">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button @click="handleGenerateAllEmbeddings" :loading="generating">
          <el-icon><Connection /></el-icon>
          批量生成向量
        </el-button>
      </template>
    </el-page-header>

    <!-- Product Info -->
    <el-card v-loading="loading" class="mb-20">
      <template #header>
        <div class="card-header">
          <span>基本信息</span>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="产品名称">{{ product?.name }}</el-descriptions-item>
        <el-descriptions-item label="版本">{{ product?.version || '-' }}</el-descriptions-item>
        <el-descriptions-item label="厂商">{{ product?.vendor || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ product?.category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="product?.is_active ? 'success' : 'info'">
            {{ product?.is_active ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(product?.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="产品描述" :span="2">
          {{ product?.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Features List -->
    <el-card v-loading="featuresLoading">
      <template #header>
        <div class="card-header">
          <span>功能列表 ({{ features.length }})</span>
          <div>
            <el-input
              v-model="searchText"
              placeholder="搜索功能"
              style="width: 200px; margin-right: 10px"
              clearable
            />
            <el-button type="primary" size="small" @click="$router.push(`/products/${productId}/edit`)">
              <el-icon><Plus /></el-icon>
              添加功能
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredFeatures" border style="width: 100%">
        <el-table-column prop="feature_name" label="功能名称" width="150" />
        <el-table-column prop="description" label="功能描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="subcategory" label="子分类" width="120" />
        <el-table-column prop="importance_level" label="重要性" width="150">
          <template #default="{ row }">
            <el-rate v-model="row.importance_level" disabled />
          </template>
        </el-table-column>
        <el-table-column label="向量状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="hasEmbedding(row) ? 'success' : 'info'" size="small">
              {{ hasEmbedding(row) ? '已生成' : '未生成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleGenerateEmbedding(row)">
              生成向量
            </el-button>
            <el-button link type="primary" @click="handleViewFeature(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProductStore } from '@/store'
import { ElMessage } from 'element-plus'
import { Edit, Connection, Plus } from '@element-plus/icons-vue'
import type { Feature } from '@/types'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const productStore = useProductStore()

const loading = ref(false)
const featuresLoading = ref(false)
const generating = ref(false)
const searchText = ref('')

const productId = computed(() => route.params.id as string)

const product = computed(() => productStore.currentProduct)
const features = computed(() => productStore.features)

const filteredFeatures = computed(() => {
  if (!searchText.value) return features.value
  return features.value.filter(f =>
    f.feature_name.includes(searchText.value) ||
    f.description.includes(searchText.value)
  )
})

onMounted(async () => {
  await loadProduct()
  await loadFeatures()
})

async function loadProduct() {
  loading.value = true
  try {
    await productStore.fetchProduct(productId.value)
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

function hasEmbedding(feature: Feature) {
  return (feature as any).has_embedding || false
}

function formatDate(date?: string) {
  return date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '-'
}

async function handleGenerateEmbedding(feature: Feature) {
  try {
    const loading = ElLoading.service({ fullscreen: true, text: '生成中...' })
    await productStore.generateFeatureEmbedding(feature.id)
    loading.close()
    ElMessage.success('向量生成成功')
    await loadFeatures()
  } catch (error) {
    ElMessage.error('向量生成失败')
  }
}

async function handleGenerateAllEmbeddings() {
  try {
    await ElMessageBox.confirm(
      `确定要为该产品的所有功能生成向量吗？共${features.value.length}个功能。`,
      '确认操作',
      { type: 'warning' }
    )

    generating.value = true
    const loading = ElLoading.service({ fullscreen: true, text: '批量生成中...' })

    await productStore.generateEmbeddingsBatch({
      product_id: productId.value
    })

    loading.close()
    ElMessage.success('批量生成成功')
    await loadFeatures()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量生成失败')
    }
  } finally {
    generating.value = false
  }
}

function handleViewFeature(feature: Feature) {
  // Could implement a detail dialog here
  ElMessage.info('功能详情: ' + feature.feature_name)
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
