/**
 * Portal Routes Configuration
 * 产品门户路由配置
 */
import { RouteRecordRaw } from 'vue-router'

export const portalRoutes: RouteRecordRaw[] = [
  {
    path: '/portal',
    name: 'PortalHome',
    component: () => import('@/views/portal/Home.vue'),
    meta: { 
      title: '产品门户',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/products',
    name: 'PortalProductList',
    component: () => import('@/views/portal/ProductList.vue'),
    meta: { 
      title: '产品中心',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/products/:id',
    name: 'PortalProductDetail',
    component: () => import('@/views/portal/ProductDetail.vue'),
    meta: { 
      title: '产品详情',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/compare',
    name: 'PortalProductCompare',
    component: () => import('@/views/portal/ProductCompare.vue'),
    meta: { 
      title: '产品对比',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/matching',
    name: 'PortalMatchingInput',
    component: () => import('@/views/portal/MatchingInput.vue'),
    meta: { 
      title: '智能匹配',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/matching/results/:id',
    name: 'PortalMatchingResult',
    component: () => import('@/views/portal/MatchingResult.vue'),
    meta: { 
      title: '匹配结果',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/matching/history',
    name: 'PortalMatchingHistory',
    component: () => import('@/views/portal/MatchingHistory.vue'),
    meta: { 
      title: '匹配历史',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/solutions',
    name: 'PortalSolutionList',
    component: () => import('@/views/portal/SolutionList.vue'),
    meta: { 
      title: '解决方案',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/solutions/:id',
    name: 'PortalSolutionDetail',
    component: () => import('@/views/portal/SolutionDetail.vue'),
    meta: { 
      title: '解决方案详情',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/resources',
    name: 'PortalResourceList',
    component: () => import('@/views/portal/ResourceList.vue'),
    meta: { 
      title: '资源中心',
      layout: 'PortalLayout'
    }
  },
  {
    path: '/portal/about',
    name: 'PortalAbout',
    component: () => import('@/views/portal/About.vue'),
    meta: { 
      title: '关于我们',
      layout: 'PortalLayout'
    }
  }
]

export default portalRoutes