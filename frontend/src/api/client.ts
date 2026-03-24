/**
 * Axios HTTP client configuration for DealDesk API.
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Create and configure the Axios instance.
 */
const createAxiosClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: 30000,
  })

  // Request interceptor - add auth token if available
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = localStorage.getItem('token')
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error: AxiosError) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor - handle auth errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        // Clear token and redirect to login
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )

  return client
}

export const apiClient = createAxiosClient()

export default apiClient
