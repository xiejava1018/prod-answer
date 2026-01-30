/**
 * Embedding configuration API
 */
import { get, post, put, del } from '@/utils/request'
import type {
  EmbeddingModelConfig,
  EmbeddingTestResult,
  EmbeddingEncodeRequest,
  EmbeddingEncodeResponse
} from '@/types'

const CONFIGS_PREFIX = '/v1/configs'
const SERVICE_PREFIX = '/v1/service'

export const embeddingsApi = {
  // Config management
  getConfigs(params?: any) {
    return get<any>(`${CONFIGS_PREFIX}/`, params)
  },

  getConfig(id: string) {
    return get<EmbeddingModelConfig>(`${CONFIGS_PREFIX}/${id}/`)
  },

  createConfig(data: Partial<EmbeddingModelConfig>) {
    return post<EmbeddingModelConfig>(`${CONFIGS_PREFIX}/`, data)
  },

  updateConfig(id: string, data: Partial<EmbeddingModelConfig>) {
    return put<EmbeddingModelConfig>(`${CONFIGS_PREFIX}/${id}/`, data)
  },

  deleteConfig(id: string) {
    return del(`${CONFIGS_PREFIX}/${id}/`)
  },

  setDefault(id: string) {
    return post<any>(`${CONFIGS_PREFIX}/${id}/set_default/`)
  },

  testConnection(id: string) {
    return post<EmbeddingTestResult>(`${CONFIGS_PREFIX}/${id}/test_connection/`)
  },

  // Service APIs
  getActiveProviders() {
    return get<any>(`${SERVICE_PREFIX}/active_providers/`)
  },

  getDefaultProvider() {
    return get<EmbeddingModelConfig>(`${SERVICE_PREFIX}/default_provider/`)
  },

  encodeTexts(data: EmbeddingEncodeRequest) {
    return post<EmbeddingEncodeResponse>(`${SERVICE_PREFIX}/encode/`, data)
  },

  getServiceInfo() {
    return get<any>(`${SERVICE_PREFIX}/service/`)
  },

  healthCheck() {
    return post<any>(`${SERVICE_PREFIX}/health_check/`)
  }
}
