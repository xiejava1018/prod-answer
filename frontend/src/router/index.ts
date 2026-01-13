/**
 * Vue Router configuration
 */
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/products',
    name: 'ProductList',
    component: () => import('@/views/products/ProductList.vue'),
    meta: { title: '产品管理' }
  },
  {
    path: '/products/create',
    name: 'ProductCreate',
    component: () => import('@/views/products/ProductForm.vue'),
    meta: { title: '创建产品' }
  },
  {
    path: '/products/:id',
    name: 'ProductDetail',
    component: () => import('@/views/products/ProductDetail.vue'),
    meta: { title: '产品详情' }
  },
  {
    path: '/products/:id/edit',
    name: 'ProductEdit',
    component: () => import('@/views/products/ProductForm.vue'),
    meta: { title: '编辑产品' }
  },
  {
    path: '/requirements',
    name: 'RequirementList',
    component: () => import('@/views/requirements/RequirementList.vue'),
    meta: { title: '需求列表' }
  },
  {
    path: '/requirements/create',
    name: 'RequirementCreate',
    component: () => import('@/views/requirements/RequirementCreate.vue'),
    meta: { title: '创建需求' }
  },
  {
    path: '/matching',
    name: 'MatchingAnalysis',
    component: () => import('@/views/matching/MatchingAnalysis.vue'),
    meta: { title: '匹配分析' }
  },
  {
    path: '/matching/results/:id',
    name: 'MatchResultDetail',
    component: () => import('@/views/matching/MatchResultDetail.vue'),
    meta: { title: '匹配结果' }
  },
  {
    path: '/settings/embeddings',
    name: 'EmbeddingSettings',
    component: () => import('@/views/settings/EmbeddingSettings.vue'),
    meta: { title: 'Embedding配置' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guard to set page title
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || '产品能力匹配系统'} - ProdAnswer`
  next()
})

export default router
