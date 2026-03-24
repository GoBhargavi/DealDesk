/**
 * DCF (Discounted Cash Flow) modeling types.
 */

export interface DCFInputs {
  deal_id: string
  company_name: string
  projection_years: number
  revenue_base: number
  revenue_growth_rates: number[]
  ebitda_margins: number[]
  capex_pct_revenue: number
  nwc_change_pct_revenue: number
  tax_rate: number
  wacc: number
  terminal_growth_rate: number
  exit_multiple: number
  net_debt: number
  shares_outstanding?: number
}

export interface DCFYearlyResult {
  year: number
  revenue: number
  ebitda: number
  ebit: number
  taxes: number
  nopat: number
  depreciation: number
  capex: number
  nwc_change: number
  fcf: number
  pv_factor: number
  pv_fcf: number
}

export interface DCFResult {
  deal_id: string
  company_name: string
  yearly_results: DCFYearlyResult[]
  sum_pv_fcf: number
  terminal_value: number
  pv_terminal_value: number
  enterprise_value: number
  net_debt: number
  equity_value: number
  implied_share_price: number | null
  sensitivity_table: number[][]
}

export interface DCFAssumptions {
  company_name: string
  revenue_growth_rates: number[]
  ebitda_margins: number[]
  capex_pct_revenue: number
  nwc_change_pct_revenue: number
  tax_rate: number
  wacc: number
  terminal_growth_rate: number
  exit_multiple: number
  rationale: {
    growth: string
    margins: string
    valuation: string
  }
}

export interface DCFAIAssistRequest {
  deal_id: string
  company_description: string
  sector: string
  recent_financials_text?: string
}

export interface WaterfallDataPoint {
  name: string
  value: number
  fill?: string
}
