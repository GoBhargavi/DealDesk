/**
 * Comps API module for comparable transaction analysis.
 */

import type { CompsResult, CompsAnalyzeRequest } from '@/types/comps'

export const compsApi = {
  /**
   * Start comps analysis and return SSE stream URL.
   * The actual streaming is handled by the useSSEStream hook.
   */
  getAnalyzeStreamUrl(): string {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/comps/analyze`
  },

  /**
   * Get cached comps result for a deal.
   */
  async getCached(dealId: string): Promise<CompsResult> {
    const response = await fetch(
      `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/comps/${dealId}`
    )
    if (!response.ok) {
      throw new Error(`Failed to fetch cached comps: ${response.statusText}`)
    }
    return response.json()
  }
}

export default compsApi
