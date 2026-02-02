<template>
  <div class="portal-home">
    <!-- Hero 区域 -->
    <section class="hero-section">
      <div class="container">
        <div class="hero-content">
          <h1 class="hero-title">
            智能安全产品能力匹配平台
          </h1>
          <p class="hero-subtitle">
            基于AI语义分析，快速找到满足需求的产品
          </p>
          <div class="hero-tags">
            <span class="tag">精准匹配</span>
            <span class="tag">智能推荐</span>
            <span class="tag">高效决策</span>
          </div>
          
          <!-- 快速匹配输入区 -->
          <div class="quick-match-area">
            <el-input
              v-model="requirementText"
              type="textarea"
              :rows="3"
              placeholder="请输入您的需求，例如：需要支持多因素认证、权限管理、审计日志的安全产品..."
              class="requirement-input"
            />
            <div class="quick-match-actions">
              <el-button 
                type="primary" 
                size="large"
                class="match-btn"
                @click="goToMatching"
              >
                <el-icon><Search /></el-icon>
                立即匹配
              </el-button>
              <el-upload
                class="upload-btn"
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFileChange"
                accept=".xlsx,.xls,.csv,.docx"
              >
                <el-button size="large">
                  <el-icon><Upload /></el-icon>
                  上传需求文件
                </el-button>
              </el-upload>
            </div>
          </div>
          
          <div class="hero-actions">
            <el-button size="large" @click="scrollToProducts">
              探索产品
            </el-button>
            <el-button size="large" @click="scrollToSolutions">
              查看解决方案
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <!-- 产品分类导航 -->
    <section class="categories-section" ref="productsSection">
      <div class="container">
        <h2 class="section-title">产品分类</h2>
        <div class="categories-grid">
          <div 
            v-for="category in categories" 
            :key="category.key"
            class="category-card"
            @click="goToCategory(category.key)"
          >
            <div class="category-icon">
              <el-icon :size="32">
                <component :is="category.icon" />
              </el-icon>
            </div>
            <h3 class="category-title">{{ category.name }}</h3>
            <p class="category-desc">{{ category.description }}</p>
            <div class="category-stats">
              <span class="product-count">{{ category.productCount }} 个产品</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 热门产品推荐 -->
    <section class="featured-products-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">热门产品推荐</h2>
          <el-button text @click="goToProducts">
            查看全部 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
        
        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="3" animated />
        </div>
        
        <div v-else-if="featuredProducts.length" class="products-grid">
          <ProductCard
            v-for="product in featuredProducts"
            :key="product.id"
            :product="product"
            @click="goToProductDetail(product.id)"
          />
        </div>
        
        <div v-else class="empty-state">
          <el-empty description="暂无推荐产品" />
        </div>
      </div>
    </section>

    <!-- 解决方案轮播 -->
    <section class="solutions-section" ref="solutionsSection">
      <div class="container">
        <h2 class="section-title">解决方案</h2>
        <div v-if="loadingSolutions" class="loading-state">
          <el-skeleton :rows="2" animated />
        </div>
        <div v-else class="solutions-carousel">
          <el-carousel :interval="4000" arrow="always" height="300px">
            <el-carousel-item v-for="solution in featuredSolutions" :key="solution.id">
              <div class="solution-card">
                <div class="solution-content">
                  <h3 class="solution-title">{{ solution.name }}</h3>
                  <p class="solution-desc">{{ solution.summary }}</p>
                  <div class="solution-meta">
                    <span class="solution-category">{{ solution.category }}</span>
                    <span class="solution-product-count">{{ solution.products.length }} 个产品</span>
                  </div>
                  <el-button type="primary" @click="goToSolution(solution.id)">
                    查看详情
                  </el-button>
                </div>
                <div class="solution-image">
                  <el-image v-if="solution.architecture_image" :src="solution.architecture_image" fit="cover" />
                  <div v-else class="image-placeholder">
                    <el-icon :size="64"><Picture /></el-icon>
                  </div>
                </div>
              </div>
            </el-carousel-item>
          </el-carousel>
        </div>
      </div>
    </section>

    <!-- 快速统计 -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalProducts }}</div>
            <div class="stat-label">产品总数</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalFeatures }}</div>
            <div class="stat-label">功能特性</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalSolutions }}</div>
            <div class="stat-label">解决方案</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ stats.totalResources }}</div>
            <div class="stat-label">资源文档</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 使用指南 -->
    <section class="guide-section">
      <div class="container">
        <h2 class="section-title">使用指南</h2>
        <div class="guide-steps">
          <div class="guide-step">
            <div class="step-number">1</div>
            <div class="step-content">
              <h3>输入需求</h3>
              <p>在上方输入框中描述您的需求，或上传需求文档</p>
            </div>
          </div>
          <div class="guide-step">
            <div class="step-number">2</div>
            <div class="step-content">
              <h3>智能匹配</h3>
              <p>AI语义分析自动匹配满足需求的产品</p>
            </div>
          </div>
          <div class="guide-step">
            <div class="step-number">3</div>
            <div class="step-content">
              <h3>查看结果</h3>
              <p>查看匹配结果，对比产品功能特性</p>
            </div>
          </div>
          <div class="guide-step">
            <div class="step-number">4</div>
            <div class="step-content">
              <h3>导出报告</h3>
              <p>导出匹配报告，分享给团队成员</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Search, Upload, ArrowRight, Picture,
  Monitor, DataAnalysis, Connection, Operation, Umbrella
} from '@element-plus/icons-vue'
import ProductCard from '@/components/portal/ProductCard.vue'
import portalAPI from '@/api/portal'

const router = useRouter()

// 数据状态
const requirementText = ref('')
const featuredProducts = ref([])
const featuredSolutions = ref([])
const loading = ref(false)
const loadingSolutions = ref(false)

// 统计数据
const stats = ref({
  totalProducts: 0,
  totalFeatures: 0,
  totalSolutions: 0,
  totalResources: 0
})

// 产品分类
const categories = [
  {
    key: 'asset_mapping',
    name: '资产测绘',
    description: '网络资产发现与管理',
    icon: Monitor,
    productCount: 0
  },
  {
    key: 'exposure_mapping',
    name: '暴露面管理',
    description: '互联网暴露面检测',
    icon: Connection,
    productCount: 0
  },
  {
    key: 'big_data',
    name: '安全大数据',
    description: '安全数据分析平台',
    icon: DataAnalysis,
    productCount: 0
  },
  {
    key: 'soar',
    name: '自动化编排',
    description: 'SOAR安全编排',
    icon: Operation,
    productCount: 0
  },
  {
    key: 'comprehensive',
    name: '综合安全',
    description: '综合安全解决方案',
    icon: Umbrella,
    productCount: 0
  }
]

// 方法
const goToMatching = () => {
  if (requirementText.value.trim()) {
    router.push({
      path: '/portal/matching',
      query: { requirement: requirementText.value }
    })
  } else {
    router.push('/portal/matching')
  }
}

const handleFileChange = (file: any) => {
  router.push({
    path: '/portal/matching',
    query: { file: file.name }
  })
}

const scrollToProducts = () => {
  const element = document.querySelector('.categories-section')
  element?.scrollIntoView({ behavior: 'smooth' })
}

const scrollToSolutions = () => {
  const element = document.querySelector('.solutions-section')
  element?.scrollIntoView({ behavior: 'smooth' })
}

const goToCategory = (category: string) => {
  router.push({
    path: '/portal/products',
    query: { subsystem_type: category }
  })
}

const goToProducts = () => {
  router.push('/portal/products')
}

const goToProductDetail = (id: string) => {
  router.push(`/portal/products/${id}`)
}

const goToSolution = (id: string) => {
  router.push(`/portal/solutions/${id}`)
}

// 加载数据
const loadFeaturedProducts = async () => {
  loading.value = true
  try {
    const res = await portalAPI.getFeaturedProducts()
    featuredProducts.value = res.data
  } catch (error) {
    console.error('Failed to load featured products:', error)
  } finally {
    loading.value = false
  }
}

const loadFeaturedSolutions = async () => {
  loadingSolutions.value = true
  try {
    const res = await portalAPI.getFeaturedSolutions()
    featuredSolutions.value = res.data
  } catch (error) {
    console.error('Failed to load featured solutions:', error)
  } finally {
    loadingSolutions.value = false
  }
}

const loadStats = async () => {
  try {
    const res = await portalAPI.getStats()
    stats.value = res.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

// 生命周期
onMounted(() => {
  loadFeaturedProducts()
  loadFeaturedSolutions()
  loadStats()
})
</script>

<style scoped lang="scss">
.portal-home {
  background: #fff;
}

.hero-section {
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  padding: 80px 0 100px;
  color: #fff;
  text-align: center;

  .hero-content {
    max-width: 800px;
    margin: 0 auto;
  }

  .hero-title {
    font-size: 48px;
    font-weight: 700;
    margin-bottom: 16px;
    line-height: 1.2;
  }

  .hero-subtitle {
    font-size: 20px;
    margin-bottom: 24px;
    opacity: 0.9;
  }

  .hero-tags {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 40px;

    .tag {
      background: rgba(255, 255, 255, 0.2);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 500;
      backdrop-filter: blur(10px);
    }
  }

  .quick-match-area {
    background: rgba(255, 255, 255, 0.1);
    padding: 24px;
    border-radius: 16px;
    backdrop-filter: blur(10px);
    margin-bottom: 32px;

    .requirement-input {
      margin-bottom: 16px;

      :deep(.el-textarea__inner) {
        background: rgba(255, 255, 255, 0.9);
        border: none;
        font-size: 16px;

        &::placeholder {
          color: #909399;
        }
      }
    }

    .quick-match-actions {
      display: flex;
      gap: 16px;
      justify-content: center;

      .match-btn {
        font-size: 16px;
        padding: 12px 32px;
        height: auto;

        .el-icon {
          margin-right: 8px;
        }
      }

      .upload-btn {
        .el-button {
          font-size: 16px;
          padding: 12px 24px;
          height: auto;

          .el-icon {
            margin-right: 8px;
          }
        }
      }
    }
  }

  .hero-actions {
    display: flex;
    gap: 16px;
    justify-content: center;

    .el-button {
      font-size: 16px;
      padding: 12px 32px;
      height: auto;
    }
  }
}

.categories-section {
  padding: 80px 0;
  background: #f8fafc;

  .section-title {
    text-align: center;
    font-size: 36px;
    font-weight: 600;
    margin-bottom: 48px;
    color: #303133;
  }

  .categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
  }

  .category-card {
    background: #fff;
    padding: 32px;
    border-radius: 16px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    border: 1px solid #e4e7ed;

    &:hover {
      transform: translateY(-8px);
      box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
      border-color: #1890ff;
    }

    .category-icon {
      width: 80px;
      height: 80px;
      margin: 0 auto 16px;
      background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }

    .category-title {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 8px;
      color: #303133;
    }

    .category-desc {
      font-size: 14px;
      color: #606266;
      margin-bottom: 16px;
      line-height: 1.5;
    }

    .category-stats {
      .product-count {
        font-size: 14px;
        color: #909399;
        font-weight: 500;
      }
    }
  }
}

.featured-products-section {
  padding: 80px 0;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 48px;

    .section-title {
      font-size: 36px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }

    .el-button {
      font-size: 16px;

      .el-icon {
        margin-left: 4px;
      }
    }
  }

  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 24px;
  }

  .loading-state {
    padding: 40px 0;
  }

  .empty-state {
    text-align: center;
    padding: 60px 0;
  }
}

.solutions-section {
  padding: 80px 0;
  background: #f8fafc;

  .section-title {
    text-align: center;
    font-size: 36px;
    font-weight: 600;
    margin-bottom: 48px;
    color: #303133;
  }

  .loading-state {
    padding: 40px 0;
  }

  .solutions-carousel {
    .solution-card {
      display: flex;
      gap: 40px;
      padding: 40px;
      height: 100%;

      .solution-content {
        flex: 1;

        .solution-title {
          font-size: 24px;
          font-weight: 600;
          margin-bottom: 16px;
          color: #303133;
        }

        .solution-desc {
          font-size: 16px;
          color: #606266;
          line-height: 1.6;
          margin-bottom: 24px;
        }

        .solution-meta {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;

          .solution-category {
            background: #1890ff;
            color: #fff;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 14px;
          }

          .solution-product-count {
            color: #909399;
            font-size: 14px;
          }
        }
      }

      .solution-image {
        width: 400px;
        height: 220px;
        border-radius: 8px;
        overflow: hidden;

        .image-placeholder {
          width: 100%;
          height: 100%;
          background: #f5f7fa;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #dcdfe6;
        }
      }
    }
  }
}

.stats-section {
  padding: 60px 0;
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  color: #fff;

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 40px;
    text-align: center;
  }

  .stat-item {
    .stat-number {
      font-size: 48px;
      font-weight: 700;
      margin-bottom: 8px;
    }

    .stat-label {
      font-size: 16px;
      opacity: 0.9;
    }
  }
}

.guide-section {
  padding: 80px 0;
  background: #fff;

  .section-title {
    text-align: center;
    font-size: 36px;
    font-weight: 600;
    margin-bottom: 48px;
    color: #303133;
  }

  .guide-steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 32px;
  }

  .guide-step {
    text-align: center;

    .step-number {
      width: 60px;
      height: 60px;
      background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: 700;
      margin: 0 auto 16px;
    }

    .step-content {
      h3 {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 8px;
        color: #303133;
      }

      p {
        font-size: 14px;
        color: #606266;
        line-height: 1.5;
      }
    }
  }
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

@media (max-width: 768px) {
  .hero-section {
    padding: 60px 0 80px;

    .hero-title {
      font-size: 32px;
    }

    .hero-subtitle {
      font-size: 18px;
    }

    .quick-match-actions {
      flex-direction: column;
    }

    .hero-actions {
      flex-direction: column;
    }
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .products-grid {
    grid-template-columns: 1fr;
  }

  .solution-card {
    flex-direction: column;

    .solution-image {
      width: 100%;
      height: 200px;
    }
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 24px;
  }

  .guide-steps {
    grid-template-columns: 1fr;
  }
}
</style>