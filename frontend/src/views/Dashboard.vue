<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- Stats Cards -->
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="32">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Actions -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/products/create')">
              <el-icon><Plus /></el-icon>
              创建产品
            </el-button>
            <el-button type="success" @click="$router.push('/requirements/create')">
              <el-icon><Upload /></el-icon>
              上传需求
            </el-button>
            <el-button type="warning" @click="$router.push('/matching')">
              <el-icon><Connection /></el-icon>
              匹配分析
            </el-button>
            <el-button @click="$router.push('/settings/embeddings')">
              <el-icon><Setting /></el-icon>
              模型配置
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统状态</span>
            </div>
          </template>
          <div class="system-status">
            <div class="status-item">
              <span class="status-label">Embedding服务:</span>
              <el-tag :type="embeddingStatus.type">{{ embeddingStatus.text }}</el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">默认模型:</span>
              <span class="status-value">{{ defaultModel }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Activities -->
    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>使用指南</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item timestamp="第一步" placement="top">
              <el-card>
                <h4>配置Embedding模型</h4>
                <p>前往"系统设置"配置OpenAI或本地Embedding模型</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="第二步" placement="top">
              <el-card>
                <h4>录入产品功能</h4>
                <p>在"产品管理"中创建产品并录入功能特性</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="第三步" placement="top">
              <el-card>
                <h4>上传能力需求</h4>
                <p>在"需求管理"中上传需求文件或直接输入文本</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="第四步" placement="top">
              <el-card>
                <h4>执行匹配分析</h4>
                <p>在"匹配分析"中执行语义匹配并查看结果</p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProductStore, useEmbeddingStore } from '@/store'
import { Document, Box, Connection, Setting, Plus, Upload } from '@element-plus/icons-vue'

const productStore = useProductStore()
const embeddingStore = useEmbeddingStore()

const stats = ref([
  {
    title: '产品总数',
    value: 0,
    icon: Box,
    color: '#409eff'
  },
  {
    title: '功能总数',
    value: 0,
    icon: Document,
    color: '#67c23a'
  },
  {
    title: '需求数',
    value: 0,
    icon: Connection,
    color: '#e6a23c'
  },
  {
    title: '匹配次数',
    value: 0,
    icon: Setting,
    color: '#f56c6c'
  }
])

const embeddingStatus = ref({
  type: 'info' as any,
  text: '检查中...'
})

const defaultModel = ref('未配置')

onMounted(async () => {
  // Load stats
  await productStore.fetchProducts()
  stats.value[0].value = productStore.total

  // Check embedding status
  try {
    await embeddingStore.fetchDefaultConfig()
    if (embeddingStore.defaultConfig) {
      embeddingStatus.value = {
        type: 'success',
        text: '正常'
      }
      defaultModel.value = embeddingStore.defaultConfig.model_name
    }
  } catch (error) {
    embeddingStatus.value = {
      type: 'danger',
      text: '未配置'
    }
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        margin-right: 15px;
      }

      .stat-info {
        flex: 1;

        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: var(--text-primary);
          line-height: 1;
          margin-bottom: 8px;
        }

        .stat-title {
          font-size: 14px;
          color: var(--text-secondary);
        }
      }
    }
  }

  .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .system-status {
    .status-item {
      display: flex;
      align-items: center;
      margin-bottom: 15px;

      &:last-child {
        margin-bottom: 0;
      }

      .status-label {
        width: 120px;
        color: var(--text-secondary);
      }

      .status-value {
        color: var(--text-primary);
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
  }
}
</style>
