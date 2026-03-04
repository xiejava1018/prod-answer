<template>
  <div class="product-list-container">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="product in products" :key="product.id">
        <el-card class="product-card" @click="viewDetail(product.id)">
          <template #header>
            <div class="card-header">
              <span class="product-name">{{ product.name }}</span>
              <el-tag v-if="product.category" size="small">{{ product.category }}</el-tag>
            </div>
          </template>
          <div class="product-info">
            <p class="product-description">{{ product.description || '暂无描述' }}</p>
            <div class="product-meta">
              <el-tag size="small" type="info">{{ product.subsystem_type }}</el-tag>
              <el-tag size="small" type="success">{{ product.vendor || '未知厂商' }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="products.length === 0" description="暂无产品数据" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

interface Product {
  id: string
  name: string
  description?: string
  category?: string
  subsystem_type?: string
  vendor?: string
}

const products = ref<Product[]>([])
const loading = ref(false)

const fetchProducts = async () => {
  loading.value = true
  try {
    const response = await fetch('http://111.228.57.2:8000/api/v1/products/')
    if (!response.ok) throw new Error('获取产品列表失败')
    const data = await response.json()
    products.value = data.results || data
  } catch (error) {
    console.error('获取产品列表失败:', error)
    ElMessage.error('获取产品列表失败')
  } finally {
    loading.value = false
  }
}

const viewDetail = (id: string) => {
  router.push(`/portal/products/${id}`)
}

onMounted(() => {
  fetchProducts()
})
</script>

<style scoped>
.product-list-container {
  padding: 20px;
}

.product-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.product-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 10px 0;
  min-height: 48px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-meta {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
</style>
