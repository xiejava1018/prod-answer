/**
 * Matching and requirements API
 */
import { get, post, upload, del } from '@/utils/request'
import type {
  CapabilityRequirement,
  MatchResult,
  MatchAnalyzeRequest,
  MatchAnalyzeResponse
} from '@/types'

const REQUIREMENTS_PREFIX = '/v1/requirements'
const MATCHING_PREFIX = '/v1/matching'

export const matchingApi = {
  // Requirement APIs
  createRequirement(data: {
    requirement_text: string
    requirement_type: 'text' | 'file'
    created_by?: string
  }) {
    return post<CapabilityRequirement>(`${REQUIREMENTS_PREFIX}/`, data)
  },

  uploadRequirement(file: File, createdBy?: string, title?: string) {
    const formData = new FormData()
    formData.append('file', file)
    if (createdBy) {
      formData.append('created_by', createdBy)
    }
    if (title) {
      formData.append('title', title)
    }
    return upload<CapabilityRequirement>(`/v1/file-uploads/upload/`, formData)
  },

  parseRequirement(data: {
    requirement_text: string
    created_by?: string
  }) {
    return post<CapabilityRequirement>(`/v1/file-uploads/parse_text/`, data)
  },

  getRequirement(id: string) {
    return get<CapabilityRequirement>(`${REQUIREMENTS_PREFIX}/${id}/`)
  },

  getRequirements(params?: any) {
    return get<any>(`${REQUIREMENTS_PREFIX}/`, params)
  },

  getRequirementItems(id: string) {
    return get<any>(`${REQUIREMENTS_PREFIX}/${id}/items/`)
  },

  processRequirement(id: string) {
    return post(`${REQUIREMENTS_PREFIX}/${id}/process/`)
  },

  getSupportedFormats() {
    return get<any>('/v1/file-uploads/supported_formats/')
  },

  deleteRequirement(id: string) {
    return del(`${REQUIREMENTS_PREFIX}/${id}/`)
  },

  // Matching APIs
  analyzeMatch(data: MatchAnalyzeRequest) {
    return post<MatchAnalyzeResponse>(`${MATCHING_PREFIX}/`, data)
  },

  getMatchResults(requirementId: string) {
    return get<MatchResult>(`${MATCHING_PREFIX}/results/${requirementId}/`)
  },

  getMatchSummary(requirementId: string) {
    return get<any>(`${MATCHING_PREFIX}/results/${requirementId}/summary/`)
  },

  exportMatchResults(requirementId: string, data: {
    format: 'excel' | 'pdf'
    include_unmatched?: boolean
  }) {
    return post(`${MATCHING_PREFIX}/export/${requirementId}/`, data)
  }
}
