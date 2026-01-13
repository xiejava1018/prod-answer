/**
 * Common type definitions
 */

export interface ApiResponse<T = any> {
  status?: string
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T = any> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface FormFieldRule {
  required?: boolean
  message?: string
  trigger?: 'blur' | 'change'
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: any) => void
}

export interface SelectOption {
  label: string
  value: any
  disabled?: boolean
}

export interface TableColumn {
  prop: string
  label: string
  width?: string | number
  minWidth?: string | number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
}
