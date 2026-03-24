/**
 * Deals API module for pipeline management.
 */

import apiClient from './client'
import type {
  Deal,
  DealListResponse,
  CreateDealRequest,
  UpdateDealRequest,
  UpdateDealStageRequest,
  Contact,
  ContactListResponse,
  CreateContactRequest
} from '@/types/deal'

export const dealsApi = {
  /**
   * List all deals with optional filtering.
   */
  async list(params?: {
    stage?: string
    sector?: string
    deal_type?: string
    skip?: number
    limit?: number
  }): Promise<DealListResponse> {
    const response = await apiClient.get('/api/v1/deals', { params })
    return response.data
  },

  /**
   * Get a single deal by ID.
   */
  async get(dealId: string): Promise<Deal> {
    const response = await apiClient.get(`/api/v1/deals/${dealId}`)
    return response.data
  },

  /**
   * Create a new deal.
   */
  async create(data: CreateDealRequest): Promise<Deal> {
    const response = await apiClient.post('/api/v1/deals', data)
    return response.data
  },

  /**
   * Update deal fields.
   */
  async update(dealId: string, data: UpdateDealRequest): Promise<Deal> {
    const response = await apiClient.patch(`/api/v1/deals/${dealId}`, data)
    return response.data
  },

  /**
   * Delete a deal.
   */
  async delete(dealId: string): Promise<void> {
    await apiClient.delete(`/api/v1/deals/${dealId}`)
  },

  /**
   * Move deal to a new stage.
   */
  async moveStage(dealId: string, stage: string): Promise<Deal> {
    const response = await apiClient.patch(
      `/api/v1/deals/${dealId}/stage`,
      { stage }
    )
    return response.data
  },

  /**
   * List contacts for a deal.
   */
  async listContacts(dealId: string): Promise<ContactListResponse> {
    const response = await apiClient.get(`/api/v1/deals/${dealId}/contacts`)
    return response.data
  },

  /**
   * Add a contact to a deal.
   */
  async addContact(dealId: string, data: CreateContactRequest): Promise<Contact> {
    const response = await apiClient.post(
      `/api/v1/deals/${dealId}/contacts`,
      data
    )
    return response.data
  }
}

export default dealsApi
