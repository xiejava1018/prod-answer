/**
 * Product related type definitions
 */

export type SubsystemType =
  | 'asset_mapping'
  | 'exposure_mapping'
  | 'big_data'
  | 'soar'
  | 'integrated'
  | 'other'
  | null

export interface Product {
  id: string
  name: string
  version?: string
  description?: string
  vendor?: string
  category?: string
  subsystem_type?: SubsystemType
  subsystem_type_display?: string
  spec_metadata?: Record<string, any>
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
  level1_function?: string
  level2_function?: string
  indicator_type?: string
  indicator_type_display?: string
  importance_level: number
  metadata?: Record<string, any>
  is_active: boolean
  has_embedding?: boolean
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
  subsystem_type?: SubsystemType
  spec_metadata?: Record<string, any>
}

export interface FeatureFormData {
  product?: string
  feature_code?: string
  feature_name: string
  description: string
  category?: string
  subcategory?: string
  level1_function?: string
  level2_function?: string
  indicator_type?: string
  importance_level?: number
}

export interface BatchImportData {
  product_id: string
  features: FeatureFormData[]
}

export interface ImportSubsystemDataRequest {
  json_file_path: string
  vendor?: string
}

export interface ImportResponse {
  status: string
  message?: string
  products_created?: number
  features_created?: number
  products_deleted?: number
  features_deleted?: number
  errors?: string[]
}

