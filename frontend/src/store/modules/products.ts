/**
 * Product store module
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { productsApi } from '@/api'
import type { Product, Feature } from '@/types'

export const useProductStore = defineStore('products', () => {
  // State
  const products = ref<Product[]>([])
  const currentProduct = ref<Product | null>(null)
  const features = ref<Feature[]>([])
  const loading = ref(false)
  const total = ref(0)

  // Actions
  async function fetchProducts(params?: any) {
    loading.value = true
    try {
      const response = await productsApi.getProducts(params)
      products.value = response.results || []
      total.value = response.count || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchProduct(id: string) {
    loading.value = true
    try {
      currentProduct.value = await productsApi.getProduct(id)
    } finally {
      loading.value = false
    }
  }

  async function fetchFeatures(productId: string, params?: any) {
    loading.value = true
    try {
      const response = await productsApi.getProductFeatures(productId, params)
      features.value = response.features || []
    } finally {
      loading.value = false
    }
  }

  async function createProduct(data: Partial<Product>) {
    const product = await productsApi.createProduct(data)
    products.value.unshift(product)
    return product
  }

  async function updateProduct(id: string, data: Partial<Product>) {
    const product = await productsApi.updateProduct(id, data)
    const index = products.value.findIndex(p => p.id === id)
    if (index !== -1) {
      products.value[index] = product
    }
    if (currentProduct.value?.id === id) {
      currentProduct.value = product
    }
    return product
  }

  async function deleteProduct(id: string) {
    await productsApi.deleteProduct(id)
    products.value = products.value.filter(p => p.id !== id)
    if (currentProduct.value?.id === id) {
      currentProduct.value = null
    }
  }

  async function addFeature(productId: string, data: Partial<Feature>) {
    const feature = await productsApi.addFeature(productId, data)
    // Refresh the features list from server to ensure data consistency
    if (productId) {
      await fetchFeatures(productId)
    }
    return feature
  }

  async function deleteFeature(id: string) {
    await productsApi.deleteFeature(id)
    features.value = features.value.filter(f => f.id !== id)
  }

  async function generateFeatureEmbedding(featureId: string, configId?: string) {
    const result = await productsApi.generateFeatureEmbedding(featureId, configId)
    // Refresh features to get updated embedding status
    if (currentProduct.value) {
      await fetchFeatures(currentProduct.value.id)
    }
    return result
  }

  async function generateEmbeddingsBatch(data: {
    feature_ids?: string[]
    product_id?: string
    config_id?: string
    regenerate?: boolean
  }) {
    const result = await productsApi.generateEmbeddingsBatch(data)
    // Refresh features to get updated embedding status
    if (data.product_id) {
      await fetchFeatures(data.product_id)
    }
    return result
  }

  function clearCurrentProduct() {
    currentProduct.value = null
    features.value = []
  }

  return {
    // State
    products,
    currentProduct,
    features,
    loading,
    total,
    // Actions
    fetchProducts,
    fetchProduct,
    fetchFeatures,
    createProduct,
    updateProduct,
    deleteProduct,
    addFeature,
    deleteFeature,
    generateFeatureEmbedding,
    generateEmbeddingsBatch,
    clearCurrentProduct
  }
})
