/**
 * DCF API module for financial modeling.
 */

import apiClient from './client'
import type { DCFInputs, DCFResult, DCFAIAssistRequest, DCFAssumptions } from '@/types/dcf'

export const dcfApi = {
  /**
   * Calculate DCF valuation synchronously.
   */
  async calculate(inputs: DCFInputs): Promise<DCFResult> {
    const response = await apiClient.post('/api/v1/dcf/calculate', inputs)
    return response.data
  },

  /**
   * Get AI assist stream URL for DCF assumptions.
   */
  getAIAssistStreamUrl(): string {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/dcf/ai-assist`
  }
}

export default dcfApi
