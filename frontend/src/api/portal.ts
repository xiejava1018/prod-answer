/**
 * 门户API接口定义
 */

import request from '@/utils/request'
import type { 
  Product, 
  ProductListParams, 
  Solution, 
  Resource,
  PortalStats 
} from '@/types/portal'

/**
 * 获取推荐产品
 */
export const getFeaturedProducts = () => {
  return request.get('/api/v1/portal/products/featured/')
}

/**
 * 获取产品列表
 */
export const getProducts = (params: ProductListParams) => {
  return request.get('/api/v1/portal/products/', { params })
}

/**
 * 获取产品详情
 */
export const getProduct = (id: string) => {
  return request.get(`/api/v1/portal/products/${id}/`)
}

/**
 * 获取产品统计信息
 */
export const getProductStats = () => {
  return request.get('/api/v1/portal/products/statistics/')
}

/**
 * 产品对比
 */
export const compareProducts = (productIds: string[]) => {
  return request.post('/api/v1/portal/products/compare/', {
    product_ids: productIds
  })
}

/**
 * 获取推荐解决方案
 */
export const getFeaturedSolutions = () => {
  return request.get('/api/v1/portal/solutions/featured/')
}

/**
 * 获取解决方案列表
 */
export const getSolutions = (params?: any) => {
  return request.get('/api/v1/portal/solutions/', { params })
}

/**
 * 获取解决方案详情
 */
export const getSolution = (id: string) => {
  return request.get(`/api/v1/portal/solutions/${id}/`)
}

/**
 * 获取资源列表
 */
export const getResources = (params?: any) => {
  return request.get('/api/v1/portal/resources/', { params })
}

/**
 * 获取门户统计数据
 */
export const getStats = () => {
  return request.get('/api/v1/portal/stats/')
}

/**
 * 记录资源下载
 */
export const downloadResource = (id: string) => {
  return request.post(`/api/v1/portal/resources/${id}/download/`)
}

export default {
  getFeaturedProducts,
  getProducts,
  getProduct,
  getProductStats,
  compareProducts,
  getFeaturedSolutions,
  getSolutions,
  getSolution,
  getResources,
  getStats,
  downloadResource
}