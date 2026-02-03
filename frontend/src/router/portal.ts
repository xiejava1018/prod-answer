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
  }
]

export default portalRoutes
