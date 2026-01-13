/**
 * Embeddings store module
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { embeddingsApi } from '@/api'
import type { EmbeddingModelConfig } from '@/types'

export const useEmbeddingStore = defineStore('embeddings', () => {
  // State
  const configs = ref<EmbeddingModelConfig[]>([])
  const defaultConfig = ref<EmbeddingModelConfig | null>(null)
  const loading = ref(false)

  // Actions
  async function fetchConfigs(params?: any) {
    loading.value = true
    try {
      const response = await embeddingsApi.getConfigs(params)
      configs.value = response.results || response || []
    } finally {
      loading.value = false
    }
  }

  async function fetchDefaultConfig() {
    try {
      defaultConfig.value = await embeddingsApi.getDefaultProvider()
    } catch (error) {
      console.error('Failed to fetch default config:', error)
    }
  }

  async function createConfig(data: Partial<EmbeddingModelConfig>) {
    const config = await embeddingsApi.createConfig(data)
    configs.value.unshift(config)
    return config
  }

  async function updateConfig(id: string, data: Partial<EmbeddingModelConfig>) {
    const config = await embeddingsApi.updateConfig(id, data)
    const index = configs.value.findIndex(c => c.id === id)
    if (index !== -1) {
      configs.value[index] = config
    }
    if (defaultConfig.value?.id === id) {
      defaultConfig.value = config
    }
    return config
  }

  async function deleteConfig(id: string) {
    await embeddingsApi.deleteConfig(id)
    configs.value = configs.value.filter(c => c.id !== id)
    if (defaultConfig.value?.id === id) {
      defaultConfig.value = null
    }
  }

  async function setDefault(id: string) {
    const response = await embeddingsApi.setDefault(id)
    await fetchConfigs()
    await fetchDefaultConfig()
    return response
  }

  async function testConnection(id: string) {
    return await embeddingsApi.testConnection(id)
  }

  return {
    // State
    configs,
    defaultConfig,
    loading,
    // Actions
    fetchConfigs,
    fetchDefaultConfig,
    createConfig,
    updateConfig,
    deleteConfig,
    setDefault,
    testConnection
  }
})
