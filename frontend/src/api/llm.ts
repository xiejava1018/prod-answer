/**
 * LLM Configuration Management API
 */
import { get, post, put, patch, del as requestDelete } from '@/utils/request'

// Create a simple axios-like interface for consistency
const request = {
  get: <T = any>(url: string, config?: any) => get<T>(url, config?.params),
  post: <T = any>(url: string, data?: any, config?: any) => post<T>(url, data),
  put: <T = any>(url: string, data?: any) => put<T>(url, data),
  patch: <T = any>(url: string, data?: any) => patch<T>(url, data),
  delete: <T = any>(url: string) => requestDelete<T>(url)
}

export interface LLMModelConfig {
  id: string
  provider: string
  model_name: string
  base_url?: string
  api_key_encrypted: string
  max_tokens: number
  temperature: number
  model_params: Record<string, any>
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface LLMTestResult {
  status: 'success' | 'failed' | 'error'
  is_connected: boolean
  response_time_ms: number
  model_info?: Record<string, any>
  error?: string
}

export interface LLMAnalysisResult {
  id: string
  requirement_item: string
  feature: string
  is_valid_match: boolean | null
  confidence_score: number
  match_reason: string
  keywords_from_requirement: string[]
  keywords_from_feature: string[]
  llm_provider: string
  llm_model: string
  total_tokens: number
  created_at: string
}

/**
 * LLM Configuration API
 */
export const llmConfigApi = {
  /**
   * Get all LLM configurations
   */
  list: (params?: { is_active?: boolean; provider?: string }) => {
    return request.get<{ count: number; providers: LLMModelConfig[] }>('/api/v1/llm/configs/', { params })
  },

  /**
   * Get LLM configuration by ID
   */
  retrieve: (id: string) => {
    return request.get<LLMModelConfig>(`/api/v1/llm/configs/${id}/`)
  },

  /**
   * Create new LLM configuration
   */
  create: (data: Partial<LLMModelConfig>) => {
    return request.post<LLMModelConfig>('/api/v1/llm/configs/', data)
  },

  /**
   * Update LLM configuration
   */
  update: (id: string, data: Partial<LLMModelConfig>) => {
    return request.put<LLMModelConfig>(`/api/v1/llm/configs/${id}/`, data)
  },

  /**
   * Partial update LLM configuration
   */
  partialUpdate: (id: string, data: Partial<LLMModelConfig>) => {
    return request.patch<LLMModelConfig>(`/api/v1/llm/configs/${id}/`, data)
  },

  /**
   * Delete LLM configuration
   */
  delete: (id: string) => {
    return request.delete(`/api/v1/llm/configs/${id}/`)
  },

  /**
   * Test LLM connection
   */
  test: (id: string) => {
    return request.post<LLMTestResult>(`/api/v1/llm/configs/${id}/test/`)
  },

  /**
   * Set as default configuration
   */
  setDefault: (id: string) => {
    return request.post<{ status: string; message: string; config: LLMModelConfig }>(
      `/api/v1/llm/configs/${id}/set_default/`
    )
  },

  /**
   * Get active providers
   */
  getActiveProviders: () => {
    return request.get<{ count: number; providers: LLMModelConfig[] }>('/api/v1/llm/active_providers/')
  },

  /**
   * Get default provider
   */
  getDefaultProvider: () => {
    return request.get<LLMModelConfig>('/api/v1/llm/default_provider/')
  }
}

/**
 * LLM Usage & Cost API
 */
export interface DailyCost {
  date: string
  total_cost: number
  total_requests: number
  total_tokens: number
  cache_hit_rate: number
  avg_response_time_ms: number
}

export interface ModelStats {
  provider: string
  model: string
  days: number
  total_requests: number
  total_tokens: number
  total_cost: number
  avg_cost: number
  avg_tokens: number
}

export interface UsageSummary {
  total_requests: number
  total_tokens: number
  total_cost: number
  cache_hit_count: number
  cache_miss_count: number
  cache_hit_rate: number
  success_rate: number
  avg_response_time_ms: number
  most_used_provider: string
  most_used_model: string
  daily_costs: DailyCost[]
  model_stats: ModelStats[]
}

export const llmUsageApi = {
  /**
   * Get usage summary
   */
  getSummary: (days: number = 7) => {
    return request.get<UsageSummary>('/api/v1/llm/usage/summary/', { params: { days } })
  },

  /**
   * Get daily cost
   */
  getDailyCost: (date: string) => {
    return request.get<DailyCost>('/api/v1/llm/usage/daily/', { params: { date } })
  },

  /**
   * Get usage by model
   */
  getByModel: (params?: { provider?: string; model?: string; days?: number }) => {
    return request.get<{ days: number; count: number; results: ModelStats[] }>('/api/v1/llm/usage/by_model/', { params })
  },

  /**
   * Get top costs
   */
  getTopCosts: (limit: number = 20) => {
    return request.get<any>('/api/v1/llm/usage/top_costs/', { params: { limit } })
  },

  /**
   * Get errors
   */
  getErrors: (limit: number = 50) => {
    return request.get<any>('/api/v1/llm/usage/errors/', { params: { limit } })
  }
}

/**
 * LLM Analysis Results API
 */
export const llmAnalysisApi = {
  /**
   * Get all analysis results
   */
  list: (params?: {
    requirement_item_id?: string
    feature_id?: string
    is_valid?: string
    min_confidence?: number
  }) => {
    return request.get<{ results: LLMAnalysisResult[]; count: number }>('/api/v1/llm/analysis-results/', { params })
  },

  /**
   * Get analysis result by ID
   */
  retrieve: (id: string) => {
    return request.get<LLMAnalysisResult>(`/api/v1/llm/analysis-results/${id}/`)
  },

  /**
   * Get analysis statistics
   */
  getStats: () => {
    return request.get<{
      total_results: number
      valid_matches: number
      invalid_matches: number
      inconclusive: number
      average_confidence: number
      provider_distribution: Array<{ llm_provider: string; count: number }>
    }>('/api/v1/llm/analysis-results/stats/')
  }
}
