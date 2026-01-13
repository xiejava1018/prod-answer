/**
 * Product related type definitions
 */

export interface Product {
  id: string
  name: string
  version?: string
  description?: string
  vendor?: string
  category?: string
  is_active: boolean
  features_count?: number
  created_at: string
  updated_at: string
}

export interface Feature {
  id: string
  product: string
  product_name?: string
  feature_code?: string
  feature_name: string
  description: string
  category?: string
  subcategory?: string
  importance_level: number
  metadata?: Record<string, any>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface FeatureEmbedding {
  id: string
  feature: string
  feature_name?: string
  feature_description?: string
  embedding?: number[]
  model_name: string
  model_version?: string
  created_at: string
}

export interface ProductFormData {
  name: string
  version?: string
  description?: string
  vendor?: string
  category?: string
}

export interface FeatureFormData {
  product?: string
  feature_code?: string
  feature_name: string
  description: string
  category?: string
  subcategory?: string
  importance_level?: number
}

export interface BatchImportData {
  product_id: string
  features: FeatureFormData[]
}
