<template>
  <div class="product-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>产品列表</span>
          <el-button type="primary" @click="$router.push('/products/create')">
            <el-icon><Plus /></el-icon>
            创建产品
          </el-button>
        </div>
      </template>

      <!-- Filter -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="搜索">
          <el-input v-model="searchText" placeholder="产品名称" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- Table -->
      <el-table :data="products" v-loading="loading" border>
        <el-table-column prop="name" label="产品名称" />
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="category" label="分类" width="150" />
        <el-table-column prop="vendor" label="厂商" width="150" />
        <el-table-column prop="features_count" label="功能数" width="100" align="center" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/products/${row.id}`)">
              查看
            </el-button>
            <el-button link type="primary" @click="$router.push(`/products/${row.id}/edit`)">
              编辑
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <el-pagination
        class="mt-20"
        background
        layout="total, sizes, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProductStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()
const productStore = useProductStore()

const loading = ref(false)
const searchText = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

const products = computed(() => productStore.products)
const total = computed(() => productStore.total)

onMounted(() => {
  fetchProducts()
})

async function fetchProducts() {
  loading.value = true
  try {
    await productStore.fetchProducts({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchText.value
    })
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchProducts()
}

function handleReset() {
  searchText.value = ''
  currentPage.value = 1
  fetchProducts()
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchProducts()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchProducts()
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm('确定要删除此产品吗？', '确认删除', {
      type: 'warning'
    })

    await productStore.deleteProduct(row.id)
    ElMessage.success('删除成功')
    fetchProducts()
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
}

.filter-form {
  margin-bottom: 20px;
}
</style>
