/**
 * Matching store module
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { matchingApi } from '@/api'
import type { CapabilityRequirement, MatchResult } from '@/types'

export const useMatchingStore = defineStore('matching', () => {
  // State
  const requirements = ref<CapabilityRequirement[]>([])
  const currentRequirement = ref<CapabilityRequirement | null>(null)
  const matchResults = ref<MatchResult | null>(null)
  const loading = ref(false)

  // Actions
  async function fetchRequirements(params?: any) {
    loading.value = true
    try {
      const response = await matchingApi.getRequirements(params)
      requirements.value = response.results || []
    } finally {
      loading.value = false
    }
  }

  async function fetchRequirement(id: string) {
    loading.value = true
    try {
      currentRequirement.value = await matchingApi.getRequirement(id)
    } finally {
      loading.value = false
    }
  }

  async function createTextRequirement(data: {
    requirement_text: string
    created_by?: string
  }, autoAnalyze?: boolean) {
    loading.value = true
    try {
      const requirement = await matchingApi.createRequirement({
        ...data,
        requirement_type: 'text',
        auto_analyze: autoAnalyze !== undefined ? autoAnalyze : true
      })
      requirements.value.unshift(requirement)
      return requirement
    } finally {
      loading.value = false
    }
  }

  async function uploadRequirement(file: File, createdBy?: string, title?: string, autoAnalyze?: boolean) {
    loading.value = true
    try {
      const requirement = await matchingApi.uploadRequirement(file, createdBy, title, autoAnalyze)
      requirements.value.unshift(requirement)
      return requirement
    } finally {
      loading.value = false
    }
  }

  async function analyzeMatch(requirementId: string, threshold?: number) {
    loading.value = true
    try {
      const response = await matchingApi.analyzeMatch({
        requirement_id: requirementId,
        threshold
      })
      return response
    } finally {
      loading.value = false
    }
  }

  async function analyzeEnhanced(
    requirementId: string,
    threshold?: number,
    llm_config_id?: string,
    llm_analysis_mode?: 'full' | 'quick'
  ) {
    loading.value = true
    try {
      const response = await matchingApi.analyzeEnhanced({
        requirement_id: requirementId,
        threshold,
        llm_config_id,
        llm_analysis_mode
      })
      return response
    } finally {
      loading.value = false
    }
  }

  async function analyzeAsync(
    requirementId: string,
    threshold?: number,
    llm_config_id?: string,
    llm_analysis_mode?: 'full' | 'quick'
  ) {
    loading.value = true
    try {
      const response = await matchingApi.analyzeAsync({
        requirement_id: requirementId,
        threshold,
        llm_config_id,
        llm_analysis_mode
      })
      return response
    } finally {
      loading.value = false
    }
  }

  async function pollTaskStatus(taskId: string, maxAttempts = 120, interval = 1000, onProgress?: (progress: number, status: string) => void) {
    let attempts = 0
    while (attempts < maxAttempts) {
      const statusData = await matchingApi.getTaskStatus(taskId)

      if (!statusData) {
        throw new Error('Task not found')
      }

      console.log(`[Poll Task ${taskId}] Status: ${statusData.status}, Progress: ${statusData.progress}%`)

      // Call progress callback if provided
      if (onProgress && typeof statusData.progress === 'number') {
        console.log(`[Poll Task] Calling onProgress with ${statusData.progress}%`)
        onProgress(statusData.progress, statusData.status)
      }

      if (statusData.status === 'completed') {
        return statusData.result
      }

      if (statusData.status === 'failed') {
        throw new Error(statusData.error || 'Task failed')
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, interval))
      attempts++
    }

    throw new Error('Task timeout')
  }

  async function fetchMatchResults(requirementId: string) {
    loading.value = true
    try {
      matchResults.value = await matchingApi.getMatchResults(requirementId)
      return matchResults.value
    } finally {
      loading.value = false
    }
  }

  function clearCurrentRequirement() {
    currentRequirement.value = null
    matchResults.value = null
  }

  return {
    // State
    requirements,
    currentRequirement,
    matchResults,
    loading,
    // Actions
    fetchRequirements,
    fetchRequirement,
    createTextRequirement,
    uploadRequirement,
    analyzeMatch,
    analyzeEnhanced,
    analyzeAsync,
    pollTaskStatus,
    fetchMatchResults,
    clearCurrentRequirement
  }
})
