/**
 * Pitch book generation types.
 */

export type PitchbookSection =
  | 'situation_overview'
  | 'company_profile'
  | 'valuation_analysis'
  | 'process_recommendations'
  | 'key_risks'

export interface PitchbookGenerateRequest {
  deal_id: string
  include_sections?: PitchbookSection[]
}

export interface PitchbookSectionContent {
  section: PitchbookSection
  content: string
}

export interface PitchbookResult {
  deal_id: string
  sections: Record<PitchbookSection, string>
  generated_at: string
}

export interface CachedPitchbook {
  deal_id: string
  sections: Record<PitchbookSection, string>
  generated_at: string
}

export interface PitchbookSSEEvent {
  event: 'section_start' | 'token' | 'section_done' | 'done' | 'error'
  data: unknown
}
