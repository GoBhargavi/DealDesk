/**
 * Comparable transactions (comps) analysis types.
 */

export interface ComparableTransaction {
  company: string
  transaction_date: string
  deal_value_usd_m: number
  revenue_usd_m: number
  ebitda_usd_m: number
  ev_revenue: number
  ev_ebitda: number
  p_e: number
}

export interface ImpliedValuation {
  low: number
  mid: number
  high: number
}

export interface CompsResult {
  deal_id: string
  target_company: string
  sector: string
  comparables: ComparableTransaction[]
  implied_valuation: ImpliedValuation
  median_ev_ebitda: number
  median_ev_revenue: number
}

export interface CompsAnalyzeRequest {
  deal_id: string
  target_company: string
  sector: string
  deal_type: string
  deal_value_usd?: number
}

export interface SensitivityCell {
  wacc: number
  exit_multiple: number
  value: number
}

export type SensitivityGrid = SensitivityCell[][]
