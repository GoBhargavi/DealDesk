/**
 * News and intelligence feed types.
 */

export type NewsSentiment = 'positive' | 'neutral' | 'negative'

export interface NewsItem {
  id: string
  headline: string
  source: string
  published_at: string
  url: string
  summary: string
  sentiment: NewsSentiment
  relevance_tags: string[]
  deal_id: string | null
}

export interface NewsListResponse {
  items: NewsItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NewsFetchRequest {
  deal_id: string
}

export interface NewsFilters {
  q?: string
  sector?: string
  deal_id?: string
  sentiment?: NewsSentiment
  page?: number
  page_size?: number
}
