/**
 * API client for DealDesk Phase 2 Settings
 * 
 * Provides functions for:
 * - LLM Provider configuration (BYOLLM)
 * - Search Provider configuration (Deep Search)
 * - MCP Server configuration
 * - Research Agent
 */

import api from '../lib/axios';
import {
  LLMConfig,
  LLMConfigCreate,
  LLMProviderInfo,
  ValidationResult,
  AgentLLMOverride,
  AgentOverrideUpdate,
  SearchConfig,
  SearchConfigCreate,
  SearchTestResult,
  MCPServerConfig,
  MCPServerConfigCreate,
  SettingsSummary,
  ResearchRequest,
  ResearchResult,
  ResearchEvent
} from '../types/settings';

// ============================================================================
// LLM Provider API
// ============================================================================

export const getLLMConfig = async (): Promise<LLMConfig | null> => {
  const response = await api.get('/settings/llm');
  return response.data;
};

export const setLLMConfig = async (config: LLMConfigCreate): Promise<LLMConfig> => {
  const response = await api.put('/settings/llm', config);
  return response.data;
};

export const getLLMProviders = async (): Promise<LLMProviderInfo[]> => {
  const response = await api.get('/settings/llm/providers');
  return response.data;
};

export const validateLLMConfig = async (config: LLMConfigCreate): Promise<ValidationResult> => {
  const response = await api.post('/settings/llm/validate', config);
  return response.data;
};

// ============================================================================
// Agent Override API
// ============================================================================

export const getAgentOverrides = async (): Promise<AgentLLMOverride[]> => {
  const response = await api.get('/settings/llm/overrides');
  return response.data;
};

export const setAgentOverride = async (
  agentName: string,
  update: AgentOverrideUpdate
): Promise<AgentLLMOverride> => {
  const response = await api.put(`/settings/llm/overrides/${agentName}`, update);
  return response.data;
};

// ============================================================================
// Search Provider API
// ============================================================================

export const getSearchConfig = async (): Promise<SearchConfig | null> => {
  const response = await api.get('/settings/search');
  return response.data;
};

export const setSearchConfig = async (config: SearchConfigCreate): Promise<SearchConfig> => {
  const response = await api.put('/settings/search', config);
  return response.data;
};

export const testSearchProvider = async (): Promise<SearchTestResult> => {
  const response = await api.post('/settings/search/test');
  return response.data;
};

// ============================================================================
// MCP Server API
// ============================================================================

export const getMCPServers = async (): Promise<MCPServerConfig[]> => {
  const response = await api.get('/settings/mcp');
  return response.data;
};

export const addMCPServer = async (config: MCPServerConfigCreate): Promise<MCPServerConfig> => {
  const response = await api.post('/settings/mcp', config);
  return response.data;
};

export const toggleMCPServer = async (serverId: string): Promise<MCPServerConfig> => {
  const response = await api.patch(`/settings/mcp/${serverId}/toggle`);
  return response.data;
};

export const deleteMCPServer = async (serverId: string): Promise<void> => {
  await api.delete(`/settings/mcp/${serverId}`);
};

// ============================================================================
// Settings Summary API
// ============================================================================

export const getSettingsSummary = async (): Promise<SettingsSummary> => {
  const response = await api.get('/settings/summary');
  return response.data;
};

// ============================================================================
// Research Agent API (SSE Streaming)
// ============================================================================

export const runResearch = (
  request: ResearchRequest,
  onEvent: (event: ResearchEvent) => void,
  onError?: (error: Error) => void
): (() => void) => {
  const eventSource = new EventSource(
    `${api.defaults.baseURL}/settings/research?data=${encodeURIComponent(JSON.stringify(request))}`
  );

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onEvent({ event: data.event, data } as ResearchEvent);
    } catch (err) {
      console.error('Failed to parse SSE event:', err);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    if (onError) {
      onError(new Error('Research stream failed'));
    }
    eventSource.close();
  };

  // Return cleanup function
  return () => {
    eventSource.close();
  };
};

// ============================================================================
// Export all settings API functions
// ============================================================================

export const settingsApi = {
  // LLM
  getLLMConfig,
  setLLMConfig,
  getLLMProviders,
  validateLLMConfig,
  // Agent Overrides
  getAgentOverrides,
  setAgentOverride,
  // Search
  getSearchConfig,
  setSearchConfig,
  testSearchProvider,
  // MCP
  getMCPServers,
  addMCPServer,
  toggleMCPServer,
  deleteMCPServer,
  // Summary
  getSettingsSummary,
  // Research
  runResearch
};
