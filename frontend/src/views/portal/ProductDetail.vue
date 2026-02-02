<template>
  <div class="product-detail-page">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-empty description="产品不存在或已下架">
        <el-button type="primary" @click="goBack">
          返回产品列表
        </el-button>
      </el-empty>
    </div>

    <!-- 产品详情 -->
    <div v-else-if="product" class="product-detail">
      <!-- 产品头部信息 -->
      <section class="product-header">
        <div class="container">
          <div class="header-content">
            <div class="product-info">
              <h1 class="product-name">{{ product.name }}</h1>
              <div class="product-meta">
                <span v-if="product.version" class="product-version">{{ product.version }}</span>
                <span v-if="product.vendor" class="product-vendor">{{ product.vendor }}</span>
                <el-tag v-if="product.subsystem_type" :type="getSubsystemType(product.subsystem_type)" size="small">
                  {{ getSubsystemLabel(product.subsystem_type) }}
                </el-tag>
                <span v-if="product.category" class="product-category">{{ product.category }}</span>
              </div>
              <p v-if="product.description" class="product-description">{{ product.description }}</p>
              <div v-if="product.key_benefits?.length" class="key-benefits">
                <h4>核心价值</h4>
                <ul>
                  <li v-for="(benefit, index) in product.key_benefits" :key="index">
                    {{ benefit }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="product-actions">
              <el-button type="primary" size="large" @click="addToCompare(product)">
                加入对比
              </el-button>
              <el-button size="large" @click="goBack">
                返回列表
              </el-button>
            </div>
          </div>
        </div>
      </section>

      <!-- 产品详情内容 -->
      <section class="product-content">
        <div class="container">
          <el-tabs v-model="activeTab" class="product-tabs">
            <!-- 功能特性 -->
            <el-tab-pane label="功能特性" name="features">
              <div class="features-section">
                <div class="section-header">
                  <h3>功能列表</h3>
                  <el-input
                    v-model="featureSearch"
                    placeholder="搜索功能"
                    clearable
                    class="feature-search"
                    style="width: 300px"
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
                
                <div v-if="filteredFeatures.length" class="feature-tree">
                  <div
                    v-for="level1 in filteredFeatures"
                    :key="level1.name"
                    class="level-1-item"
                  >
                    <div class="level-1-header" @click="toggleLevel1(level1.name)">
                      <el-icon class="expand-icon">
                        <ArrowRight v-if="!expandedLevel1.includes(level1.name)" />
                        <ArrowDown v-else />
                      </el-icon>
                      <span class="level-1-name">{{ level1.name }}</span>
                      <el-tag size="small" type="info">
                        {{ level1.children.length }} 个功能
                      </el-tag>
                    </div>
                    
                    <div v-if="expandedLevel1.includes(level1.name)" class="level-1-children">
                      <div
                        v-for="level2 in level1.children"
                        :key="level2.name"
                        class="level-2-item"
                      >
                        <div class="level-2-header" @click="toggleLevel2(`${level1.name}-${level2.name}`)">
                          <el-icon class="expand-icon">
                            <ArrowRight v-if="!expandedLevel2.includes(`${level1.name}-${level2.name}`)" />
                            <ArrowDown v-else />
                          </el-icon>
                          <span class="level-2-name">{{ level2.name }}</span>
                          <el-tag v-if="level2.children?.length" size="small" type="info">
                            {{ level2.children.length }} 个子功能
                          </el-tag>
                        </div>
                        
                        <div v-if="expandedLevel2.includes(`${level1.name}-${level2.name}`) && level2.children?.length" class="level-2-children">
                          <div
                            v-for="level3 in level2.children"
                            :key="level3.name"
                            class="level-3-item"
                          >
                            <div class="level-3-content">
                              <span class="level-3-name">{{ level3.name }}</span>
                              <div class="level-3-meta">
                                <el-tag v-if="level3.indicator_type" size="small" :type="getIndicatorType(level3.indicator_type)">
                                  {{ getIndicatorLabel(level3.indicator_type) }}
                                </el-tag>
                                <el-rate
                                  v-if="level3.importance_level"
                                  :model-value="level3.importance_level"
                                  disabled
                                  show-score
                                  text-color="#ff9900"
                                  :score-template="`{value}分`"
                                  class="importance-rate"
                                />
                              </div>
                            </div>
                            <p v-if="level3.description" class="level-3-description">{{ level3.description }}</p>
                          </div>
                        </div>
                        
                        <p v-if="level2.description && !level2.children?.length" class="level-2-description">
                          {{ level2.description }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div v-else class="empty-features">
                  <el-empty description="暂无功能数据" />
                </div>
              </div>
            </el-tab-pane>

            <!-- 技术规格 -->
            <el-tab-pane label="技术规格" name="specs">
              <div class="specs-section">
                <div v-if="specMetadataGroups && Object.keys(specMetadataGroups).length" class="spec-groups">
                  <div
                    v-for="(specs, group) in specMetadataGroups"
                    :key="group"
                    class="spec-group"
                  >
                    <h4 class="group-title">{{ group }}</h4>
                    <div class="spec-items">
                      <div
                        v-for="spec in specs"
                        :key="spec.name"
                        class="spec-item"
                      >
                        <span class="spec-name">{{ spec.name }}</span>
                        <span class="spec-value">{{ spec.value }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-specs">
                  <el-empty description="暂无技术规格数据" />
                </div>
              </div>
            </el-tab-pane>

            <!-- 统计信息 -->
            <el-tab-pane label="统计信息" name="stats">
              <div class="stats-section">
                <div class="stats-grid">
                  <div class="stat-card">
                    <div class="stat-value">{{ product.feature_count || 0 }}</div>
                    <div class="stat-label">功能总数</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value">{{ product.view_count || 0 }}</div>
                    <div class="stat-label">浏览次数</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value">{{ product.download_count || 0 }}</div>
                    <div class="stat-label">下载次数</div>
                  </div>
                </div>
                
                <div v-if="featureStats" class="feature-stats">
                  <h4>功能分布</h4>
                  <div class="stats-charts">
                    <div class="chart-item">
                      <h5>指标类型分布</h5>
                      <div id="indicatorTypeChart" style="width: 100%; height: 300px"></div>
                    </div>
                    <div class="chart-item">
                      <h5>重要性等级分布</h5>
                      <div id="importanceLevelChart" style="width: 100%; height: 300px"></div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- 相关产品 -->
            <el-tab-pane label="相关产品" name="related">
              <div class="related-products-section">
                <div v-if="relatedProducts.length" class="related-products">
                  <ProductCard
                    v-for="relatedProduct in relatedProducts"
                    :key="relatedProduct.id"
                    :product="relatedProduct"
                    @click="goToProductDetail(relatedProduct.id)"
                  />
                </div>
                <div v-else class="empty-related">
                  <el-empty description="暂无相关产品" />
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, ArrowRight, ArrowDown } from '@element-plus/icons-vue'
import ProductCard from '@/components/portal/ProductCard.vue'
import portalAPI from '@/api/portal'
import type { Product } from '@/types/portal'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const error = ref(false)
const product = ref<Product | null>(null)
const relatedProducts = ref<Product[]>([])
const activeTab = ref('features')
const featureSearch = ref('')
const expandedLevel1 = ref<string[]>([])
const expandedLevel2 = ref<string[]>([])

// 计算属性
const features = computed(() => {
  if (!product.value?.features) return []
  return product.value.features
})

const filteredFeatures = computed(() => {
  if (!features.value.length) return []
  
  const searchTerm = featureSearch.value.toLowerCase()
  
  return features.value.filter(level1 => {
    // 搜索一级功能
    if (level1.name.toLowerCase().includes(searchTerm)) return true
    
    // 搜索二级功能
    if (level1.children?.some(level2 => 
      level2.name.toLowerCase().includes(searchTerm) ||
      level2.children?.some(level3 => level3.name.toLowerCase().includes(searchTerm))
    )) return true
    
    return false
  })
})

const specMetadataGroups = computed(() => {
  if (!product.value?.spec_metadata) return {}
  
  const groups: Record<string, Array<{name: string, value: any}>> = {}
  
  for (const [key, value] of Object.entries(product.value.spec_metadata)) {
    // 简单的分组逻辑（可以根据实际需求调整）
    let group = '其他'
    if (key.includes('性能') || key.includes('速度') || key.includes('容量')) {
      group = '性能指标'
    } else if (key.includes('系统') || key.includes('环境') || key.includes('平台')) {
      group = '系统要求'
    } else if (key.includes('部署') || key.includes('安装') || key.includes('配置')) {
      group = '部署信息'
    }
    
    if (!groups[group]) groups[group] = []
    groups[group].push({ name: key, value })
  }
  
  return groups
})

const featureStats = computed(() => {
  if (!features.value.length) return null
  
  const stats = {
    indicatorTypes: {} as Record<string, number>,
    importanceLevels: {} as Record<string, number>
  }
  
  // 统计指标类型
  const countIndicatorTypes = (items: any[]) => {
    items.forEach(item => {
      if (item.indicator_type) {
        stats.indicatorTypes[item.indicator_type] = (stats.indicatorTypes[item.indicator_type] || 0) + 1
      }
      if (item.children) {
        countIndicatorTypes(item.children)
      }
    })
  }
  
  // 统计重要性等级
  const countImportanceLevels = (items: any[]) => {
    items.forEach(item => {
      if (item.importance_level) {
        const level = item.importance_level.toString()
        stats.importanceLevels[level] = (stats.importanceLevels[level] || 0) + 1
      }
      if (item.children) {
        countImportanceLevels(item.children)
      }
    })
  }
  
  features.value.forEach(level1 => {
    countIndicatorTypes([level1])
    countImportanceLevels([level1])
    if (level1.children) {
      level1.children.forEach(level2 => {
        countIndicatorTypes([level2])
        countImportanceLevels([level2])
        if (level2.children) {
          countIndicatorTypes(level2.children)
          countImportanceLevels(level2.children)
        }
      })
    }
  })
  
  return stats
})

// 方法
const loadProduct = async () => {
  try {
    loading.value = true
    const res = await portalAPI.getProduct(route.params.id as string)
    product.value = res.data
    
    // 加载相关产品
    await loadRelatedProducts()
    
    // 初始化图表
    if (featureStats.value) {
      initCharts()
    }
  } catch (err) {
    console.error('Failed to load product:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const loadRelatedProducts = async () => {
  try {
    // 这里可以根据实际需求加载相关产品
    // 例如：同类别、同厂商的产品
    relatedProducts.value = []
  } catch (err) {
    console.error('Failed to load related products:', err)
  }
}

const initCharts = () => {
  // 指标类型分布图
  const indicatorTypeChart = echarts.init(document.getElementById('indicatorTypeChart'))
  const indicatorTypeOption = {
    title: {
      text: '指标类型分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    series: [{
      type: 'pie',
      radius: '50%',
      data: Object.entries(featureStats.value?.indicatorTypes || {}).map(([type, count]) => ({
        name: getIndicatorLabel(type),
        value: count
      }))
    }]
  }
  indicatorTypeChart.setOption(indicatorTypeOption)
  
  // 重要性等级分布图
  const importanceLevelChart = echarts.init(document.getElementById('importanceLevelChart'))
  const importanceLevelOption = {
    title: {
      text: '重要性等级分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: Object.keys(featureStats.value?.importanceLevels || {}).sort()
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'bar',
      data: Object.entries(featureStats.value?.importanceLevels || {})
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([, count]) => count)
    }]
  }
  importanceLevelChart.setOption(importanceLevelOption)
}

const toggleLevel1 = (name: string) => {
  const index = expandedLevel1.value.indexOf(name)
  if (index > -1) {
    expandedLevel1.value.splice(index, 1)
  } else {
    expandedLevel1.value.push(name)
  }
}

const toggleLevel2 = (key: string) => {
  const index = expandedLevel2.value.indexOf(key)
  if (index > -1) {
    expandedLevel2.value.splice(index, 1)
  } else {
    expandedLevel2.value.push(key)
  }
}

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

const getIndicatorType = (type?: string) => {
  const typeMap: Record<string, string> = {
    'product_function': 'success',
    'performance': 'warning',
    'security': 'danger',
    'reliability': 'info',
    'usability': ''
  }
  return typeMap[type || ''] || 'info'
}

const getIndicatorLabel = (type?: string) => {
  const labelMap: Record<string, string> = {
    'product_function': '产品功能',
    'performance': '性能',
    'security': '安全',
    'reliability': '可靠性',
    'usability': '易用性'
  }
  return labelMap[type || ''] || type || '未知'
}

const addToCompare = (product: Product) => {
  // 实现加入对比逻辑
  console.log('Add to compare:', product)
}

const goToProductDetail = (id: string) => {
  router.push(`/portal/products/${id}`)
}

const goBack = () => {
  router.back()
}

// 生命周期
onMounted(() => {
  loadProduct()
})
</script>

<style scoped lang="scss">
.product-detail-page {
  background: #f8fafc;
  min-height: 100vh;
}

.loading-container,
.error-container {
  padding: 60px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.product-header {
  background: #fff;
  padding: 40px 0;
  border-bottom: 1px solid #e4e7ed;

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 40px;

    .product-info {
      flex: 1;
      min-width: 0;

      .product-name {
        font-size: 32px;
        font-weight: 700;
        margin: 0 0 16px 0;
        color: #303133;
        line-height: 1.3;
      }

      .product-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 20px;
        align-items: center;

        .product-version {
          font-size: 16px;
          color: #909399;
          background: #f5f7fa;
          padding: 4px 12px;
          border-radius: 4px;
        }

        .product-vendor {
          font-size: 16px;
          color: #606266;
          font-weight: 500;
        }

        .product-category {
          font-size: 14px;
          color: #909399;
          background: #f0f2f5;
          padding: 4px 12px;
          border-radius: 4px;
        }
      }

      .product-description {
        font-size: 16px;
        line-height: 1.6;
        color: #606266;
        margin-bottom: 24px;
      }

      .key-benefits {
        h4 {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 12px;
          color: #303133;
        }

        ul {
          margin: 0;
          padding-left: 20px;

          li {
            font-size: 14px;
            line-height: 1.6;
            color: #606266;
            margin-bottom: 8px;

            &:last-child {
              margin-bottom: 0;
            }
          }
        }
      }
    }

    .product-actions {
      display: flex;
      flex-direction: column;
      gap: 12px;
      flex-shrink: 0;
    }
  }
}

.product-content {
  padding: 40px 0;

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
  }

  .product-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: 32px;
    }

    :deep(.el-tabs__item) {
      font-size: 16px;
      padding: 0 24px;
      height: 48px;
      line-height: 48px;
    }
  }
}

.features-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    h3 {
      font-size: 20px;
      font-weight: 600;
      margin: 0;
      color: #303133;
    }
  }

  .feature-tree {
    .level-1-item {
      margin-bottom: 16px;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      overflow: hidden;

      &:last-child {
        margin-bottom: 0;
      }

      .level-1-header {
        display: flex;
        align-items: center;
        padding: 16px 20px;
        background: #f5f7fa;
        cursor: pointer;
        transition: background 0.3s;

        &:hover {
          background: #ebeef5;
        }

        .expand-icon {
          margin-right: 12px;
          color: #909399;
          transition: transform 0.3s;
        }

        .level-1-name {
          flex: 1;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }

      .level-1-children {
        background: #fff;
        border-top: 1px solid #e4e7ed;

        .level-2-item {
          border-bottom: 1px solid #f0f2f5;

          &:last-child {
            border-bottom: none;
          }

          .level-2-header {
            display: flex;
            align-items: center;
            padding: 12px 20px 12px 48px;
            cursor: pointer;
            transition: background 0.3s;

            &:hover {
              background: #f5f7fa;
            }

            .expand-icon {
              margin-right: 8px;
              color: #c0c4cc;
              font-size: 14px;
            }

            .level-2-name {
              flex: 1;
              font-size: 14px;
              font-weight: 500;
              color: #606266;
            }
          }

          .level-2-description {
            padding: 8px 20px 12px 68px;
            font-size: 13px;
            color: #909399;
            line-height: 1.5;
            margin: 0;
          }

          .level-2-children {
            background: #fafafa;
            border-top: 1px solid #f0f2f5;

            .level-3-item {
              padding: 12px 20px 12px 68px;
              border-bottom: 1px solid #f0f2f5;

              &:last-child {
                border-bottom: none;
              }

              .level-3-content {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 16px;
                margin-bottom: 8px;

                .level-3-name {
                  flex: 1;
                  font-size: 14px;
                  font-weight: 500;
                  color: #303133;
                }

                .level-3-meta {
                  display: flex;
                  gap: 8px;
                  align-items: center;
                  flex-shrink: 0;

                  .importance-rate {
                    :deep(.el-rate__text) {
                      font-size: 12px;
                    }
                  }
                }
              }

              .level-3-description {
                margin: 8px 0 0 0;
                font-size: 13px;
                color: #909399;
                line-height: 1.5;
              }
            }
          }
        }
      }
    }
  }

  .empty-features {
    padding: 60px 0;
  }
}

.specs-section {
  .spec-groups {
    .spec-group {
      margin-bottom: 32px;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      overflow: hidden;

      &:last-child {
        margin-bottom: 0;
      }

      .group-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        padding: 16px 20px;
        background: #f5f7fa;
        color: #303133;
        border-bottom: 1px solid #e4e7ed;
      }

      .spec-items {
        padding: 16px 20px;
        background: #fff;

        .spec-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid #f0f2f5;

          &:last-child {
            border-bottom: none;
          }

          .spec-name {
            font-size: 14px;
            color: #606266;
            font-weight: 500;
          }

          .spec-value {
            font-size: 14px;
            color: #303133;
            font-weight: 600;
            text-align: right;
            max-width: 50%;
            word-break: break-word;
          }
        }
      }
    }
  }

  .empty-specs {
    padding: 60px 0;
  }
}

.stats-section {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 24px;
    margin-bottom: 40px;

    .stat-card {
      background: #fff;
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 24px;
      text-align: center;
      transition: all 0.3s;

      &:hover {
        border-color: #1890ff;
        box-shadow: 0 4px 16px rgba(24, 144, 255, 0.1);
      }

      .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #1890ff;
        margin-bottom: 8px;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
        font-weight: 500;
      }
    }
  }

  .feature-stats {
    h4 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 24px;
      color: #303133;
    }

    .stats-charts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 32px;

      .chart-item {
        background: #fff;
        border: 1px solid #e4e7ed;
        border-radius: 8px;
        padding: 24px;

        h5 {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 20px;
          color: #303133;
          text-align: center;
        }
      }
    }
  }
}

.related-products-section {
  .related-products {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 24px;
  }

  .empty-related {
    padding: 60px 0;
  }
}

@media (max-width: 768px) {
  .product-header {
    .header-content {
      flex-direction: column;
      gap: 24px;

      .product-info {
        .product-name {
          font-size: 24px;
        }
      }

      .product-actions {
        width: 100%;
        flex-direction: row;

        .el-button {
          flex: 1;
        }
      }
    }
  }

  .features-section {
    .feature-tree {
      .level-1-item {
        .level-1-children {
          .level-2-item {
            .level-2-header {
              padding-left: 32px;
            }

            .level-2-children {
              .level-3-item {
                .level-3-content {
                  flex-direction: column;
                  align-items: flex-start;
                  gap: 8px;
                }
              }
            }
          }
        }
      }
    }
  }

  .stats-section {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .feature-stats {
      .stats-charts {
        grid-template-columns: 1fr;
      }
    }
  }
}
</style>
