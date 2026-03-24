/**
 * Documents API module for file management.
 */

import apiClient from './client'
import type {
  Document,
  DocumentListResponse,
  DocumentUploadResponse,
  DocumentAnalysisResult
} from '@/types/document'

export const documentsApi = {
  /**
   * List all documents for a deal.
   */
  async list(dealId: string): Promise<DocumentListResponse> {
    const response = await apiClient.get(`/api/v1/documents/${dealId}`)
    return response.data
  },

  /**
   * Get a single document by ID.
   */
  async get(documentId: string): Promise<Document> {
    const response = await apiClient.get(`/api/v1/documents/detail/${documentId}`)
    return response.data
  },

  /**
   * Upload a document for a deal.
   */
  async upload(
    file: File,
    dealId: string,
    fileType: string
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('deal_id', dealId)
    formData.append('file_type', fileType)

    const response = await apiClient.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * Delete a document.
   */
  async delete(documentId: string): Promise<void> {
    await apiClient.delete(`/api/v1/documents/${documentId}`)
  },

  /**
   * Get document analysis stream URL.
   */
  getAnalyzeStreamUrl(documentId: string): string {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/documents/${documentId}/analyze`
  }
}

export default documentsApi
