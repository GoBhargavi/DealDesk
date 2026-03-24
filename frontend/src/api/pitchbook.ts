/**
 * Pitchbook API module for generating pitch books.
 */

import type { PitchbookGenerateRequest, CachedPitchbook } from '@/types/pitchbook'

export const pitchbookApi = {
  /**
   * Get pitchbook generation stream URL.
   */
  getGenerateStreamUrl(): string {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/pitchbook/generate`
  },

  /**
   * Get cached pitchbook for a deal.
   */
  async getCached(dealId: string): Promise<CachedPitchbook> {
    const response = await fetch(
      `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/pitchbook/${dealId}`
    )
    if (!response.ok) {
      throw new Error(`Failed to fetch cached pitchbook: ${response.statusText}`)
    }
    return response.json()
  }
}

export default pitchbookApi
