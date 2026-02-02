<template>
  <div class="product-card" @click="handleClick">
    <div class="card-header">
      <div class="product-info">
        <h3 class="product-name">{{ product.name }}</h3>
        <span v-if="product.version" class="product-version">{{ product.version }}</span>
      </div>
      <div class="product-vendor">
        <span class="vendor-label">厂商</span>
        <span class="vendor-name">{{ product.vendor || '未知厂商' }}</span>
      </div>
    </div>

    <div class="card-body">
      <p class="product-description">
        {{ product.description || '暂无描述' }}
      </p>

      <div class="product-tags">
        <el-tag
          v-for="tag in displayTags"
          :key="tag"
          size="small"
          class="product-tag"
        >
          {{ tag }}
        </el-tag>
      </div>

      <div class="product-meta">
        <div class="meta-item">
          <span class="meta-label">子系统</span>
          <el-tag 
            size="small" 
            :type="getSubsystemType(product.subsystem_type)"
            class="subsystem-tag"
          >
            {{ getSubsystemLabel(product.subsystem_type) }}
          </el-tag>
        </div>
        <div class="meta-item">
          <span class="meta-label">功能数</span>
          <span class="meta-value">{{ product.feature_count || 0 }}</span>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <div class="product-stats">
        <span class="stat-item">
          <el-icon><View /></el-icon>
          {{ product.view_count || 0 }}
        </span>
        <span class="stat-item">
          <el-icon><Download /></el-icon>
          {{ product.download_count || 0 }}
        </span>
      </div>
      <div class="card-actions">
        <el-button 
          type="primary" 
          size="small"
          class="view-detail-btn"
          @click.stop="viewDetail"
        >
          查看详情
        </el-button>
        <el-button 
          size="small"
          class="compare-btn"
          @click.stop="addToCompare"
        >
          加入对比
        </el-button>
      </div>
    </div>

    <!-- 推荐标签 -->
    <div v-if="product.is_featured" class="featured-badge">
      <el-tag type="danger" size="small" effect="dark">
        推荐
      </el-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { View, Download } from '@element-plus/icons-vue'

interface Product {
  id: string
  name: string
  version?: string
  vendor?: string
  description?: string
  subsystem_type?: string
  feature_count?: number
  view_count?: number
  download_count?: number
  is_featured?: boolean
  key_features?: string[]
}

interface Props {
  product: Product
}

const props = defineProps<Props>()
const router = useRouter()

const emit = defineEmits<{
  (e: 'click', product: Product): void
  (e: 'add-to-compare', product: Product): void
}>()

// 显示的tags（最多3个）
const displayTags = computed(() => {
  const features = props.product.key_features || []
  return features.slice(0, 3)
})

// 获取子系统类型样式
const getSubsystemType = (type?: string) => {
  const typeMap: Record<string, string> = {
    'asset_mapping': 'success',
    'exposure_mapping': 'warning',
    'big_data': 'info',
    'soar': 'danger',
    'comprehensive': ''
  }
  return typeMap[type || ''] || 'info'
}

// 获取子系统标签
const getSubsystemLabel = (type?: string) => {
  const labelMap: Record<string, string> = {
    'asset_mapping': '资产测绘',
    'exposure_mapping': '暴露面管理',
    'big_data': '安全大数据',
    'soar': '自动化编排',
    'comprehensive': '综合安全'
  }
  return labelMap[type || ''] || '其他'
}

// 点击卡片
const handleClick = () => {
  emit('click', props.product)
}

// 查看详情
const viewDetail = () => {
  router.push(`/portal/products/${props.product.id}`)
}

// 加入对比
const addToCompare = () => {
  emit('add-to-compare', props.product)
  // 可以在这里添加提示
  // ElMessage.success('已加入对比列表')
}
</script>

<style scoped lang="scss">
.product-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
    border-color: #1890ff;
  }

  .featured-badge {
    position: absolute;
    top: 16px;
    right: 16px;
  }
}

.card-header {
  margin-bottom: 16px;

  .product-info {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;

    .product-name {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }

    .product-version {
      font-size: 14px;
      color: #909399;
      background: #f5f7fa;
      padding: 2px 8px;
      border-radius: 4px;
    }
  }

  .product-vendor {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;

    .vendor-label {
      color: #909399;
    }

    .vendor-name {
      color: #606266;
      font-weight: 500;
    }
  }
}

.card-body {
  flex: 1;
  margin-bottom: 16px;

  .product-description {
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    margin-bottom: 16px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .product-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;

    .product-tag {
      margin: 0;
    }
  }

  .product-meta {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .meta-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;

      .meta-label {
        color: #909399;
      }

      .meta-value {
        color: #303133;
        font-weight: 500;
      }

      .subsystem-tag {
        margin: 0;
      }
    }
  }
}

.card-footer {
  border-top: 1px solid #e4e7ed;
  padding-top: 16px;

  .product-stats {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #909399;

    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }
  }

  .card-actions {
    display: flex;
    gap: 8px;

    .view-detail-btn {
      flex: 1;
    }

    .compare-btn {
      flex: 1;
    }
  }
}

@media (max-width: 768px) {
  .product-card {
    padding: 16px;
  }

  .card-header {
    .product-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;

      .product-name {
        font-size: 16px;
      }
    }
  }

  .card-footer {
    .card-actions {
      flex-direction: column;

      .view-detail-btn,
      .compare-btn {
        width: 100%;
      }
    }
  }
}
</style>