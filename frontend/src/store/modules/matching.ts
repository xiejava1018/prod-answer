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
  }) {
    loading.value = true
    try {
      const requirement = await matchingApi.createRequirement({
        ...data,
        requirement_type: 'text'
      })
      requirements.value.unshift(requirement)
      return requirement
    } finally {
      loading.value = false
    }
  }

  async function uploadRequirement(file: File, createdBy?: string, title?: string) {
    loading.value = true
    try {
      const requirement = await matchingApi.uploadRequirement(file, createdBy, title)
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
    fetchMatchResults,
    clearCurrentRequirement
  }
})
