/**
 * Axios HTTP client configuration
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// Create axios instance
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000, // 5 minutes - increased for large file matching
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
service.interceptors.request.use(
  (config) => {
    // Add authentication token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
service.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.error || error.message || '请求失败'

    // Show error message
    ElMessage.error(message)

    // Handle specific status codes
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
      ElMessage.error('权限不足')
    } else if (error.response?.status === 404) {
      ElMessage.error('资源不存在')
    } else if (error.response?.status === 500) {
      ElMessage.error('服务器错误')
    }

    return Promise.reject(error)
  }
)

export default service

/**
 * Generic request wrapper
 */
export function request<T = any>(config: AxiosRequestConfig): Promise<T> {
  return service.request<T>(config)
}

export function get<T = any>(url: string, params?: any): Promise<T> {
  return service.get<T>(url, { params })
}

export function post<T = any>(url: string, data?: any): Promise<T> {
  return service.post<T>(url, data)
}

export function put<T = any>(url: string, data?: any): Promise<T> {
  return service.put<T>(url, data)
}

export function del<T = any>(url: string, params?: any): Promise<T> {
  return service.delete<T>(url, { params })
}

export function upload<T = any>(url: string, formData: FormData): Promise<T> {
  return service.post<T>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
