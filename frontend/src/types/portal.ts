/**
 * 门户相关类型定义
 */

// 产品类型
export interface Product {
  id: string
  name: string
  version?: string
  vendor?: string
  description?: string
  subsystem_type?: string
  category?: string
  is_featured?: boolean
  is_on_portal?: boolean
  sort_weight?: number
  thumbnail?: string
  banner_image?: string
  tagline?: string
  key_benefits?: string[]
  target_industries?: string[]
  view_count?: number
  download_count?: number
  portal_published_at?: string
  created_at?: string
  updated_at?: string
  // 扩展字段
  feature_count?: number
  key_features?: string[]
}

// 产品列表参数
export interface ProductListParams {
  page?: number
  page_size?: number
  search?: string
  subsystem_type?: string
  category?: string
  vendor?: string
  ordering?: string
  is_featured?: boolean
}

// 解决方案类型
export interface Solution {
  id: string
  name: string
  solution_type: 'industry' | 'scenario' | 'use_case'
  category: string
  summary: string
  pain_points?: string[]
  architecture?: string
  architecture_image?: string
  benefits?: string[]
  case_study_title?: string
  case_study_content?: string
  case_study_results?: Record<string, any>
  products: string[] // 产品ID列表
  is_featured?: boolean
  is_active?: boolean
  sort_weight?: number
  view_count?: number
  published_at?: string
  created_at?: string
  updated_at?: string
}

// 资源类型
export interface Resource {
  id: string
  title: string
  resource_type: 'document' | 'whitepaper' | 'case_study' | 'video' | 'datasheet'
  product?: string // 产品ID
  file?: string
  file_size?: number
  description?: string
  excerpt?: string
  cover_image?: string
  duration?: string
  download_count?: number
  is_active?: boolean
  published_at?: string
  created_at?: string
  updated_at?: string
}

// 门户统计数据
export interface PortalStats {
  total_products: number
  total_features: number
  total_solutions: number
  total_resources: number
  total_views?: number
  total_downloads?: number
}

// 产品对比结果
export interface ProductComparison {
  products: Product[]
  common_features: string[]
  unique_features: {
    [productId: string]: string[]
  }
  feature_coverage: {
    [productId: string]: number
  }
}

// 功能特性
export interface Feature {
  id: string
  product: string
  level1_function?: string
  level2_function?: string
  level3_function?: string
  description?: string
  indicator_type?: string
  importance_level?: number
  spec_metadata?: Record<string, any>
  created_at?: string
  updated_at?: string
}

// 访问日志
export interface PortalViewLog {
  id: string
  content_type: 'product' | 'solution' | 'resource'
  object_id: string
  ip_address: string
  user_agent?: string
  referer?: string
  country?: string
  region?: string
  city?: string
  created_at?: string
}

// API 响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  pagination?: {
    total: number
    page: number
    page_size: number
    total_pages: number
  }
}

// 分页数据
export interface PaginatedData<T> {
  count: number
  results: T[]
  next?: string
  previous?: string
}

// 筛选选项
export interface FilterOption {
  label: string
  value: string
  count?: number
}

// 排序选项
export interface SortOption {
  label: string
  value: string
  field: string
  order: 'asc' | 'desc'
}