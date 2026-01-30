<template>
  <div class="settings-index">
    <el-page-header @back="$router.back()" class="mb-20">
      <template #content>
        系统设置
      </template>
    </el-page-header>

    <el-row :gutter="20">
      <!-- Embedding Settings Card -->
      <el-col :span="8" class="mb-20">
        <el-card class="setting-card" shadow="hover" @click="navigateTo('/settings/embeddings')">
          <div class="card-content">
            <div class="card-icon" style="background: #ecf5ff">
              <el-icon size="32" color="#409eff"><Connection /></el-icon>
            </div>
            <div class="card-info">
              <h3>Embedding模型配置</h3>
              <p>配置和管理向量嵌入模型，用于语义匹配</p>
              <div class="card-stats">
                <el-tag size="small" type="info">{{ embeddingStats.count }} 个配置</el-tag>
                <el-tag v-if="embeddingStats.active" size="small" type="success">{{ embeddingStats.active }} 个活跃</el-tag>
              </div>
            </div>
            <el-icon class="arrow-icon" size="20"><ArrowRight /></el-icon>
          </div>
        </el-card>
      </el-col>

      <!-- LLM Settings Card -->
      <el-col :span="8" class="mb-20">
        <el-card class="setting-card" shadow="hover" @click="navigateTo('/settings/llm')">
          <div class="card-content">
            <div class="card-icon" style="background: #f0f9ff">
              <el-icon size="32" color="#67c23a"><MagicStick /></el-icon>
            </div>
            <div class="card-info">
              <h3>LLM模型配置</h3>
              <p>配置和管理大语言模型，用于智能增强分析</p>
              <div class="card-stats">
                <el-tag size="small" type="info">{{ llmStats.count }} 个配置</el-tag>
                <el-tag v-if="llmStats.active" size="small" type="success">{{ llmStats.active }} 个活跃</el-tag>
              </div>
            </div>
            <el-icon class="arrow-icon" size="20"><ArrowRight /></el-icon>
          </div>
        </el-card>
      </el-col>

      <!-- Cost Monitoring Card -->
      <el-col :span="8" class="mb-20">
        <el-card class="setting-card" shadow="hover" @click="navigateTo('/settings/costs')">
          <div class="card-content">
            <div class="card-icon" style="background: #fef0f0">
              <el-icon size="32" color="#f56c6c"><Money /></el-icon>
            </div>
            <div class="card-info">
              <h3>成本监控</h3>
              <p>查看LLM使用成本和统计信息</p>
              <div class="card-stats">
                <el-tag size="small" type="warning">最近7天</el-tag>
                <el-tag size="small" type="success">${{ costStats.totalCost }}</el-tag>
              </div>
            </div>
            <el-icon class="arrow-icon" size="20"><ArrowRight /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Quick Info -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon><InfoFilled /></el-icon>
            快速说明
          </span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Embedding模型">
          用于将文本转换为向量，支持语义相似度匹配。推荐使用 OpenAI text-embedding-3-small 或 Sentence-Transformers。
        </el-descriptions-item>
        <el-descriptions-item label="LLM模型">
          用于智能语义分析，提高匹配准确度。支持 OpenAI GPT、ZhipuAI GLM、阿里云 Qwen 等模型。
        </el-descriptions-item>
        <el-descriptions-item label="成本监控" :span="2">
          实时跟踪LLM API调用的token使用量和成本，帮助控制预算。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Connection,
  MagicStick,
  Money,
  ArrowRight,
  InfoFilled
} from '@element-plus/icons-vue'

const router = useRouter()

const embeddingStats = ref({
  count: 0,
  active: 0
})

const llmStats = ref({
  count: 0,
  active: 0
})

const costStats = ref({
  totalCost: '0.0000'
})

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    // Load embedding stats
    const embeddingRes = await fetch('/api/v1/configs/')
    const embeddingData = await embeddingRes.json()
    embeddingStats.value = {
      count: embeddingData.count || 0,
      active: embeddingData.results?.filter((r: any) => r.is_active).length || 0
    }

    // Load LLM stats
    const llmRes = await fetch('/api/v1/llm/configs/')
    const llmData = await llmRes.json()
    llmStats.value = {
      count: llmData.count || 0,
      active: llmData.providers?.filter((r: any) => r.is_active).length || 0
    }

    // Load cost stats
    const costRes = await fetch('/api/v1/llm/usage/summary/?days=7')
    const costData = await costRes.json()
    costStats.value = {
      totalCost: costData.total_cost?.toFixed(4) || '0.0000'
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

function navigateTo(path: string) {
  router.push(path)
}
</script>

<style scoped>
.settings-index {
  padding: 20px;
}

.setting-card {
  cursor: pointer;
  transition: all 0.3s;
}

.setting-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-info {
  flex: 1;
}

.card-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-info p {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

.card-stats {
  display: flex;
  gap: 8px;
}

.arrow-icon {
  color: #909399;
  flex-shrink: 0;
}

.info-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.mb-20 {
  margin-bottom: 20px;
}
</style>
