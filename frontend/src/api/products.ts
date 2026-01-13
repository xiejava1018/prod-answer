/**
 * Product management API
 */
import { get, post, put, del } from '@/utils/request'
import type {
  Product,
  ProductFormData,
  Feature,
  FeatureFormData,
  BatchImportData
} from '@/types'

const API_PREFIX = '/v1/products'
const FEATURES_PREFIX = '/v1/features'

export const productsApi = {
  // Product APIs
  getProducts(params?: any) {
    return get<any>(`${API_PREFIX}/`, params)
  },

  getProduct(id: string) {
    return get<Product>(`${API_PREFIX}/${id}/`)
  },

  createProduct(data: ProductFormData) {
    return post<Product>(`${API_PREFIX}/`, data)
  },

  updateProduct(id: string, data: Partial<ProductFormData>) {
    return put<Product>(`${API_PREFIX}/${id}/`, data)
  },

  deleteProduct(id: string) {
    return del(`${API_PREFIX}/${id}/`)
  },

  // Feature APIs
  getProductFeatures(productId: string, params?: any) {
    return get<any>(`${API_PREFIX}/${productId}/features/`, params)
  },

  addFeature(productId: string, data: FeatureFormData) {
    return post<Feature>(`${API_PREFIX}/${productId}/add_feature/`, data)
  },

  batchImportFeatures(data: BatchImportData) {
    return post<any>(`${API_PREFIX}/batch_import/`, data)
  },

  getFeatures(params?: any) {
    return get<any>(`${FEATURES_PREFIX}/`, params)
  },

  getFeature(id: string) {
    return get<Feature>(`${FEATURES_PREFIX}/${id}/`)
  },

  updateFeature(id: string, data: Partial<FeatureFormData>) {
    return put<Feature>(`${FEATURES_PREFIX}/${id}/`, data)
  },

  deleteFeature(id: string) {
    return del(`${FEATURES_PREFIX}/${id}/`)
  },

  // Embedding APIs
  generateFeatureEmbedding(id: string, configId?: string) {
    return post(`${FEATURES_PREFIX}/${id}/generate_embedding/`, {
      config_id: configId
    })
  },

  generateEmbeddingsBatch(data: {
    feature_ids?: string[]
    product_id?: string
    config_id?: string
    regenerate?: boolean
  }) {
    return post(`${FEATURES_PREFIX}/generate_embeddings_batch/`, data)
  }
}
