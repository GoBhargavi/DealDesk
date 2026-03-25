/**
 * TypeScript types for DealDesk Phase 2 Settings
 * 
 * Includes types for:
 * - LLM Provider configuration (BYOLLM)
 * - Search Provider configuration (Deep Search)
 * - MCP Server configuration
 * - Agent LLM overrides
 */

// ============================================================================
// LLM Provider Types
// ============================================================================

export type LLMProvider = 'anthropic' | 'openai' | 'google' | 'azure_openai' | 'ollama';

export interface LLMConfig {
  id: string;
  provider: LLMProvider;
  model_id: string;
  api_key_masked?: string | null;
  base_url?: string | null;
  api_version?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LLMConfigCreate {
  provider: LLMProvider;
  model_id: string;
  api_key?: string;
  base_url?: string;
  api_version?: string;
  is_active?: boolean;
}

export interface LLMProviderInfo {
  id: LLMProvider;
  label: string;
  models: string[];
  required_fields: string[];
  optional_fields: string[];
}

export interface ValidationResult {
  valid: boolean;
  message: string;
}

// ============================================================================
// Agent Override Types
// ============================================================================

export type AgentName = 'comps' | 'dcf' | 'news' | 'document' | 'pitchbook' | 'research';

export interface AgentLLMOverride {
  id: string;
  agent_name: AgentName;
  llm_config_id: string;
  is_active: boolean;
  llm_config?: LLMConfig;
  created_at: string;
}

export interface AgentOverrideUpdate {
  llm_config_id?: string;
  is_active?: boolean;
}

// ============================================================================
// Search Provider Types
// ============================================================================

export type SearchProvider = 'tavily' | 'perplexity' | 'exa';

export interface SearchConfig {
  id: string;
  provider: SearchProvider;
  api_key_masked?: string | null;
  max_results_per_query: number;
  max_queries_per_task: number;
  enable_full_page_fetch: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SearchConfigCreate {
  provider: SearchProvider;
  api_key?: string;
  max_results_per_query?: number;
  max_queries_per_task?: number;
  enable_full_page_fetch?: boolean;
  is_active?: boolean;
}

export interface SearchTestResult {
  success: boolean;
  message: string;
  result_count?: number;
}

// ============================================================================
// MCP Server Types
// ============================================================================

export type MCPServerType = 'sec_edgar' | 'financial_data' | 'news' | 'slack' | 'custom';

export interface MCPServerConfig {
  id: string;
  name: string;
  server_type: MCPServerType;
  endpoint_url: string;
  auth_token_masked?: string | null;
  is_active: boolean;
  metadata: Record<string, unknown>;
  is_connected: boolean;
  tool_count: number;
  created_at: string;
  updated_at: string;
}

export interface MCPServerConfigCreate {
  name: string;
  server_type: MCPServerType;
  endpoint_url: string;
  auth_token?: string;
  is_active?: boolean;
  metadata?: Record<string, unknown>;
}

export interface MCPServerStatus {
  server_type: MCPServerType;
  name: string;
  is_connected: boolean;
  tool_count: number;
  last_error?: string;
}

// ============================================================================
// Settings Summary
// ============================================================================

export interface SettingsSummary {
  llm_config: LLMConfig | null;
  search_config: SearchConfig | null;
  mcp_servers: MCPServerConfig[];
  agent_overrides: AgentLLMOverride[];
}

// ============================================================================
// Research Agent Types
// ============================================================================

export interface ResearchRequest {
  deal_id: string;
  query: string;
  context?: Record<string, unknown>;
}

export interface ResearchSource {
  url: string;
  title: string;
  source_name: string;
  published_date?: string;
  relevance_score: number;
}

export interface ResearchResult {
  query: string;
  summary: string;
  key_findings: string[];
  sources: ResearchSource[];
  confidence: 'high' | 'medium' | 'low';
  caveats?: string;
  data_source: 'web_research' | 'llm_generated';
}

// ============================================================================
// SSE Event Types for Deep Search
// ============================================================================

export interface ResearchStepEvent {
  step: 'generating_queries' | 'searching' | 'fetching_sources' | 'synthesising' | 'done';
  message: string;
  query_count?: number;
  source_count?: number;
}

export interface ResearchDoneEvent {
  step: 'done';
  source_count: number;
  query_count: number;
}

export interface AgentErrorEvent {
  message: string;
  code: string;
}

export type ResearchEvent = 
  | { event: 'research_step'; data: ResearchStepEvent }
  | { event: 'research_done'; data: ResearchDoneEvent }
  | { event: 'agent_error'; data: AgentErrorEvent }
  | { event: 'research_complete'; data: ResearchResult };
