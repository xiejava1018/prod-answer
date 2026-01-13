/**
 * Embedding related type definitions
 */

export interface EmbeddingModelConfig {
  id: string
  model_name: string
  model_type: 'openai' | 'huggingface' | 'sentence-transformers' | 'local' | 'openai-compatible'
  model_type_display?: string
  provider: string
  provider_name?: 'openai' | 'siliconflow' | 'zhipuai' | 'qwen' | 'sentence-transformers' | 'other'
  provider_name_display?: string
  base_url?: string
  api_endpoint?: string
  api_key_encrypted?: string
  has_api_key?: boolean
  dimension: number
  model_params?: Record<string, any>
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface EmbeddingTestResult {
  status: string
  is_connected: boolean
  model_info?: {
    model_name: string
    dimension: number
    provider: string
  }
  error?: string
}

export interface EmbeddingEncodeRequest {
  texts: string[]
  config_id?: string
}

export interface EmbeddingEncodeResponse {
  status: string
  count: number
  dimension: number
  embeddings: number[][]
}
