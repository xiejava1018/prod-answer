/**
 * Matching related type definitions
 */

export interface RequirementItem {
  id: string
  item_text: string
  item_order: number
  created_at: string
}

export interface CapabilityRequirement {
  id: string
  session_id: string
  requirement_text?: string
  requirement_type: 'text' | 'file'
  source_file_name?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_by?: string
  items_count?: number
  items?: RequirementItem[]
  created_at: string
  updated_at: string
}

export interface MatchRecord {
  id: string
  requirement: string
  requirement_item: string
  requirement_item_text?: string
  feature: string
  feature_name?: string
  feature_description?: string
  product_name?: string
  similarity_score: number
  match_status: 'matched' | 'partial_matched' | 'unmatched'
  threshold_used: number
  rank: number
  metadata?: Record<string, any>
  created_at: string
}

export interface MatchResult {
  requirement_id: string
  results: {
    matched: MatchRecord[]
    partial_matched: MatchRecord[]
    unmatched: MatchRecord[]
  }
  statistics: {
    total_items: number
    total_matches: number
    matched: number
    partial_matched: number
    unmatched: number
    avg_similarity: number
    max_similarity: number
    min_similarity: number
  }
}

export interface MatchAnalyzeRequest {
  requirement_id: string
  threshold?: number
  product_ids?: string[]
  limit?: number
}

export interface MatchAnalyzeResponse {
  requirement_id: string
  status: string
  summary: {
    total_items: number
    total_matches: number
    matched: number
    partial_matched: number
    unmatched: number
  }
  processing_time: number
}
