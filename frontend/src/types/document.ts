/**
 * Document management types.
 */

export type DocumentType = 'CIM' | 'NDA' | 'Financial' | 'Other'
export type DocumentStatus = 'Uploading' | 'Processing' | 'Ready' | 'Error'

export interface Document {
  id: string
  deal_id: string
  filename: string
  file_type: DocumentType
  s3_key: string
  status: DocumentStatus
  extracted_text: string | null
  summary: string | null
  key_risks: string[]
  key_terms: Record<string, unknown>
  created_at: string
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

export interface DocumentUploadResponse {
  document: Document
  message: string
}

export interface DocumentRisk {
  risk: string
  severity: 'High' | 'Medium' | 'Low'
  detail: string
}

export interface DocumentAnalysisResult {
  document_id: string
  document_type_detected: string
  summary: string
  key_risks: DocumentRisk[]
  key_terms: Record<string, unknown>
}
