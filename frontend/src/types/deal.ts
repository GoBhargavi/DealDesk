/**
 * Deal types for the pipeline management system.
 */

export type DealStage =
  | 'Origination'
  | 'NDA Signed'
  | 'Diligence'
  | 'IOI'
  | 'LOI'
  | 'Exclusivity'
  | 'Signing'
  | 'Closing'
  | 'Closed'
  | 'Dead'

export type DealType = 'M&A' | 'LBO' | 'IPO' | 'Restructuring' | 'Equity Raise'

export interface Deal {
  id: string
  name: string
  target_company: string
  acquirer_company: string
  deal_type: DealType
  stage: DealStage
  deal_value_usd: number | null
  sector: string
  region: string
  expected_close_date: string | null
  lead_banker: string
  assigned_team: string[]
  created_at: string
  updated_at: string
  notes: string
}

export interface DealListResponse {
  deals: Deal[]
  total: number
}

export interface CreateDealRequest {
  name: string
  target_company: string
  acquirer_company: string
  deal_type: DealType
  stage?: DealStage
  deal_value_usd?: number
  sector: string
  region: string
  expected_close_date?: string
  lead_banker: string
  assigned_team?: string[]
  notes?: string
}

export interface UpdateDealRequest {
  name?: string
  target_company?: string
  acquirer_company?: string
  deal_type?: DealType
  stage?: DealStage
  deal_value_usd?: number
  sector?: string
  region?: string
  expected_close_date?: string
  lead_banker?: string
  assigned_team?: string[]
  notes?: string
}

export interface UpdateDealStageRequest {
  stage: DealStage
}

export interface Contact {
  id: string
  name: string
  title: string
  company: string
  email: string
  phone: string | null
  is_counterparty: boolean
  deal_id: string
  created_at: string
}

export interface CreateContactRequest {
  name: string
  title: string
  company: string
  email: string
  phone?: string
  is_counterparty?: boolean
}

export interface ContactListResponse {
  contacts: Contact[]
  total: number
}
