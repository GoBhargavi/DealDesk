/**
 * News API module for intelligence feed.
 */

import apiClient from './client'
import type { NewsListResponse, NewsFilters, NewsItem } from '@/types/news'

export const newsApi = {
  /**
   * List news items with filtering and pagination.
   */
  async list(filters?: NewsFilters): Promise<NewsListResponse> {
    const response = await apiClient.get('/api/v1/news', { params: filters })
    return response.data
  },

  /**
   * Get news fetch stream URL for a deal.
   */
  getFetchStreamUrl(): string {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/news/fetch-for-deal`
  }
}

export default newsApi
